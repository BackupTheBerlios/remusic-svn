"""Collection classes are used to make searches in the MySQL database.

A collection defines a subset of the data in the Audiostore MySQL database.
Collections form a hierarchical structure to create further refined
subsets, such as:

  Genre('rock')
    Artist('Nick Cave')
      Album('Murder Ballads')
      
"""

import os
import logging
import posixpath
import re
import stat
import string
import time
import types

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

import MySQLdb.cursors
import sqlquery

import db_audiostore
#from query import *

from sqlquery import AND, OR, REGEXP, EQUAL, COUNT

logger = logging.getLogger("remus.audiostore.mysql")


_fs_root = None

def audiostore_file_root(root):
    """Path in the file system where audiostore files can be found, such
    as the xslt transformation script and others."""
    global _fs_root
    _fs_root = root


_db_to_fn = string.maketrans(" ", "_")
_fn_to_db = string.maketrans("_", " ")

#
# Translate between file names and SQL column values
#
def mk_filename(path):
    return path.replace("?", "  q") \
           .replace("/", "\\") \
           .replace("&", " and ") \
           .replace("(", " p ") \
           .replace(")", " d ") \
           .translate(_db_to_fn).lower()

def mk_sqlname( path):
    return path.translate(_fn_to_db) \
           .replace(" d ", ")") \
           .replace(" p ", "(") \
           .replace("  and  ", " & ") \
           .replace("\\", "/") \
           .replace("  q", "?")


class Collection(object):

    tables = ()
    fields = ()
    group_by = None
    order_by = None

    field_map = {
        'song'    : db_audiostore.remus_audio_objects_au_title,
        'artist'  : db_audiostore.remus_artists_art_name,
        'album'   : db_audiostore.remus_albums_alb_name,
#        'album_id': db_audiostore.remus_audio_objects_au_album,
#        'artist_id':db_audiostore.remus_albums_alb_artist,
        'length'  : db_audiostore.remus_audio_objects_au_length,
        }

    def __init__(self, parent=None, query=None, store=None):
        self.parent = parent
        self.query = query or (parent and parent.query)
        self.store = store or parent.store
        self.db = self.store.db
        self.cursor = None
        self.updates = {}
        self.is_updated = False
        self.old_values = {}

    def __setitem__(self, item, value):
        assert item in self.field_map.keys()
        self.updates[item] = value
        self.is_updated = True

    def name(self):
        return "UNKNOWN"
    
    def rename(self, old_names, new_names, coll=None):
        if not coll:
            coll = self
        if old_names:
            if old_names[-1] != new_names[-1]:
                self._rename(mk_sqlname(new_names[-1]), coll)
            self.parent.rename(old_names[:-1], new_names[:-1], coll)

    def _rename(self, newname, coll):
        assert False, "can't rename %s" % self.__class__

    def cwd(self):
        """Return the 'current working directory', which this hierarchy
        represents"""
        if self.parent:
            return posixpath.join(self.parent.cwd(), self.name())
        else:
            return posixpath.join("/", self.name())

    def isdir(self):
        if not self.cursor:
            self.select()

        isdir = self.cursor.rowcount > 1
        self.cursor.close()
        self.cursor = None
        return isdir

    def content_type(self):
        return "text/html"

    def open(self, mode, request=None):
        logger.info("Trying to open %s", self.cwd())
        if mode and mode[0] == 'w':
            # Someone is saving a file!
            return AudioSaver(self)
        assert False

    def stat(self, request=None):
        if self.select() > 0:
            stat = (0444, 0, 1, 1, os.getuid(), os.getgid(), 0,
                    time.time(), time.time(), time.time())
        else:
            raise IOError, "file not found"

        if self.cursor:
            self.cursor.close()
            self.cursor = None
        return stat

    def subcollection(self, name):
        logger.info("Looking for subcollection %s", name)
        if name == "songs":
            return SongsColl(self)
        elif name == "search":
            return SearchColl(self)
        elif name == "list":
            return PlaylistColl(self)
        elif name == "dirlist":
            return DirlistColl(self)
        elif name.startswith("--song--"):
            return SongId(self, name)
        elif name.find('--') != -1:
            fields = name.split("--")
            return SearchResultSong(self, fields)
        else:
            return None

    def songs(self):
        """Return AudioObjects for all matching songs"""
        songs = Playlist(self)
        songs.select(fields=[db_audiostore.remus_audio_objects_au_id])
        import audiostore
        return [ audiostore.AudioObject(self.store, x['au_id'])
                 for x in songs.cursor ]

    def search(self, query, fields=None):
        if self.query:
            query = AND(self.query, query)
        coll = Collection(self, query)
        if fields:
            coll.fields = fields
        return coll

    def select(self, cursorclass=MySQLdb.cursors.DictCursor, **kw):
        if kw.has_key('fields'):
            fields = kw['fields']
        else:
            fields = self.fields or self.parent.fields

        if kw.has_key('order_by'):
            order_by = kw['order_by']
        else:
            order_by = self.order_by

        if kw.has_key('group_by'):
            group_by = kw['group_by']
        else:
            group_by = self.group_by

        selection = sqlquery.Select()
        for field in fields:
            selection.addcolumn(field)

        # Make sure all 'order_by' fields are present in the query.
        # This isn't necessarily the case if the user passed a custom
        # field list.
        
        if order_by:
            order_by = [ e for e in order_by
                         if type(e) in types.StringTypes 
                         or e.table in selection.gettables() ]

        sql = selection.select(
            query=self.query,
            order_by=order_by,
            group_by=group_by)

        logger.info("Performing SQL: %s", sql)
        logger.info("Order by: %s, %s, %s", self.order_by, order_by, kw)

        self.cursor = self.db.cursor(cursorclass)
        return self.cursor.execute(sql)


    def update(self):

        selection = sqlquery.Select()
        selection.addcolumn(db_audiostore.remus_audio_objects_au_audio_clip)
        selection.addcolumn(db_audiostore.remus_audio_objects_au_content_type)

        # Get the list of file names, and update the audio file
        # before updating the database
        cursor = self.db.cursor()
        sql = selection.select(query=self.query)
        count = cursor.execute(sql)

        for filename, mimetype in cursor:
            audiostore.mime_map[mimetype].update(filename, self.updates)

        # Update the database

        # First, figure out which tables we're updating.
        # For now, support only one table, so make sure all updated
        # fields belong to the same one
        update_tables = [ self.field_map[key].table
                          for key in self.updates.keys() ]

        table = update_tables[0]
        for t in update_tables[1:]:
            if t != table:
                raise "Can't update multiple tables yet"


        # Create a selection, and add the table's primary key column
        # to the selection (NOTE: We're making the assumption the table
        # has a primary key, and this key is a single column. While this
        # isn't true in general, it's safe in this context: every remus
        # database has a single column primary key)
        selection = sqlquery.Select()
        selection.addcolumn(table.primary_key)

        sql = selection.select(query=self.query)
        count = cursor.execute(sql)

        # Ok, we know which table to update, and the above query told us
        # which rows to update. Trim off duplicate values:
        import sets
        rows = sets.Set([ key for (key,) in cursor.fetchall() ])

        # Construct the column update
        set = [ "%s = %s" % (self.field_map[key].name, self.db.literal(value))
                for key, value in self.updates.items() ]

        # Create 'where' clause from the rows
        where = " or ".join([ "%s = %s" % (table.primary_key.name, key)
                              for key in rows ])
        
        sql = "UPDATE %s SET %s WHERE %s" % \
              (table.name, ", ".join(set), where)

        count = cursor.execute(sql)
        cursor.close()
        return count

    def remove(self, limit="LIMIT 1"):
        selection = sqlquery.Select()
        selection.addcolumn(db_audiostore.remus_audio_objects_au_id)

        sql = selection.select(query)
        sql += limit

        cursor = self.db.cursor()

        count = cursor.execute(sql)
    
        for au_id in cursor:
            audioobject = audiostore.AudioObject(self.store, au_id)
            logger.info("removing audio clip %s", au_id)
            audioobject.remove()


class SearchColl(Collection):

    fields = (
        db_audiostore.remus_audio_objects.au_title,
        db_audiostore.remus_albums.alb_name,
        db_audiostore.remus_artists.art_name,
        db_audiostore.remus_audio_objects.au_length,
        db_audiostore.remus_art_alb_map.artalb_id,
        )

    op_map = {
        '=' : sqlquery.REGEXP,
        '<' : sqlquery.LESS_THAN,
        '>' : sqlquery.GREATER_THAN,
        '<=': sqlquery.LESS_EQUAL,
        '>=': sqlquery.GREATER_EQUAL,
        }

    op_regex = '(%s)' % '|'.join(op_map.keys())
        
    def __init__(self, parent):
        Collection.__init__(self, parent, parent.query)

    def name(self):
        return "search"

    def subcollection(self, search):
        return self.search(self.parse_query(search),
                           fields = self.fields)

    def parse_query(self, query):
        "Parse string and build a query object"

        # queries are separated with ';'
        queries = query.split(';')

        # a query can be of the form "field=<regexp>"
        # or just <regexp>, which means artist, album and title
        # will be matched against the regexp.
        my_queries = []
        for q in queries:
            try:
                field, comp, regex = re.split(self.op_regex, q)
                my_queries.append(self.op_map[comp](self.field_map[field],
                                                    regex))
            except ValueError:
                my_queries.append(
                    OR(OR(REGEXP(db_audiostore.remus_audio_objects_au_title, q),
                          REGEXP(db_audiostore.remus_albums_alb_name, q)),
                       REGEXP(db_audiostore.remus_artists_art_name, q)))
        return reduce(AND, my_queries)


class SongsColl(Collection):

    fields = (
        db_audiostore.remus_audio_objects.au_title,
        db_audiostore.remus_audio_objects.au_length
        )

    def __init__(self, parent):
        Collection.__init__(self, parent, parent.query)

    def name(self):
        return "songs"


class Song(Collection):

    # Not really a collection, this is a single song
    fields = (
        db_audiostore.remus_audio_objects.au_title,
        db_audiostore.remus_audio_objects.au_length
        )

    def __init__(self, parent, songtitle):
        self.title = songtitle
        query = EQUAL(db_audiostore.remus_audio_objects_au_title,
                      songtitle)
        if parent.query:
            query = AND(parent.query, query)
        Collection.__init__(self, parent, query)

    def isdir(self):
        return False

    def name(self):
        return self.title

    def stat(self, request=None):
        count = self.select(fields=(db_audiostore.remus_audio_objects_au_audio_clip,))
        if count != 1:
            raise IOError, "file not found"

        stat = os.stat(self.cursor.fetchone()["au_audio_clip"])
        self.cursor.close()
        self.cursor = None
        return stat

    def content_type(self):
        count = self.select(fields=(db_audiostore.remus_audio_objects_au_content_type,))
        if count != 1:
            raise IOError, "file not found"

        content_type = self.cursor.fetchone()["au_content_type"]
        self.cursor.close()
        self.cursor = None
        return content_type

    def open(self, mode, request=None):
        if mode and mode[0] == 'w':
            # Someone is saving a file!
            return AudioSaver(self)
        else:
            # Open the audio file, and return file object here
            count = self.select(fields=(db_audiostore.remus_audio_objects_au_audio_clip,))
            if count != 1:
                raise IOError, "file not found"
            
            filename = self.cursor.fetchone()["au_audio_clip"]
            self.cursor.close()
            self.cursor = None
            return open(filename)


class SongId(Song):

    def __init__(self, parent, songid):
        self.id = songid[8:]
        query = EQUAL(db_audiostore.remus_audio_objects_au_id, self.id)
        Collection.__init__(self, parent, query)

    def name(self):
        return "--song--%s" % self.id


class SearchResultSong(Song):

    def __init__(self, parent, songtuple):
        "The 'songtuple' matches the fields in SearchColl.fields"
        self.songtuple = songtuple
        query = [ EQUAL(field, value)
                  for field, value in map(None, SearchColl.fields, songtuple) ]
        query = reduce(AND, query)
        if parent.query:
            query = AND(parent.query, query)
        Collection.__init__(self, parent, query)

    def name(self):
        return "--".join(self.songtuple)
    

class PlaylistColl(Collection):
    """Return a playlist file in some format.

    A playlist is a generic term for any type of file containing a list
    of songs. Through the PlaylistColl class, specific playlist formats
    are obtained by looking for a matching XSLT stylesheet in the
    styles catalog, and applying them to a standard XML file produced
    from the query"""

    def name(self):
        return "list"
    
    def isdir(self):
        return True

    def subcollection(self, name):
        """The name of the subcollection is used to look up an XSLT
        file to apply."""
        subcol = super(PlaylistColl, self).subcollection(name)
        if not subcol:
            xsl_stylesheet = os.path.join(_fs_root, "styles", "%s.xsl" % name)
            return IndexXMLAudioList(self, xsl_stylesheet)
        else:
            return subcol

class DirlistColl(Collection):

    def name(self):
        return "dirlist"

    def isdir(self):
        return True

    def subcollection(self, name):
        """The name of the subcollection is used to look up an XSLT
        file to apply."""
        subcol = super(DirlistColl, self).subcollection(name)
        if not subcol:
            xsl_stylesheet = os.path.join(_fs_root, "styles", "%s.xsl" % name)
            return IndexXMLDirList(self, xsl_stylesheet)
        else:
            return subcol


class IndexXMLBase(Collection):

    def __init__(self, parent, xsltfile):
        if parent.parent.order_by:
            self.order_by = parent.parent.order_by
        super(IndexXMLBase, self).__init__(parent)
        self.file = None
        self.xsltfile = xsltfile

    def create_file(self, request=None):
        # Build an index page
        xmlfile = StringIO()

        # FIXME: Shouldn't hardcode this
        urlroot = "/music/"

        if request:
            inet, addr, port = request.getHost()
            if port == 80:
                hostport = ''
            else:
                hostport = ':%d' % port

            import urllib

            server =  urllib.quote('http%s://%s%s' % (
                request.isSecure() and 's' or '',
                request.getRequestHostname(),
                hostport), "/:")
            path = request.path[len(urlroot):]

        else:
            server = "http://unknown.org"
            path = self.cwd()

        print >> xmlfile, '<?xml version="1.0" encoding="utf-8"?>\n'

        cnt = self.select()
        print >> xmlfile, '<%s length="%s">\n' % (self.document_type, cnt)

        # Strip away "list/<stylesheet>", if present
        if posixpath.basename(posixpath.dirname(path)) == "list":
            path = posixpath.dirname(posixpath.dirname(path)) + "/"
        path = xml_fix_string(path).replace("%20", ' ') or '/'
        if path != '/':
            path = "".join([ (elem and "<d>%s</d>" % elem)
                             for elem in path.split("/") ])

        print >> xmlfile, '  <path>%s</path>\n' % path

        self.write_body(xmlfile)

        print >> xmlfile, "</%s>\n" % self.document_type

        self.cursor.close()
        self.cursor = None

        # Perform xslt transformation on the file
        from commands import getstatusoutput
        import remus.i18n
        import libxslt
        import libxml2

        params = {
            'audiostore.root':      "'%s'"   % urlroot,
            'audiostore.url':       "'%s%s'" % (server, urlroot),
            'l10n.gentext.language':"'%s'"   % remus.i18n.current_lang(),
            }

        xsltfile = open(self.xsltfile).read()

        # If the XSLT file contains the <menu/> element, create menu
        # and insert it.
        if xsltfile.find("<menu/>") != -1:
            import remus.webserver.menu

            menu = remus.webserver.menu.create_basemenu()
            widget = remus.webserver.menu.Menu(menu)
            menu = widget.generate(None, remus.webserver.menu.document).toxml()

            xsltfile = xsltfile.replace("<menu/>", menu)

            # Update the encoding to the appropriate one, since the menu
            # contains translated text.
            charset = remus.i18n.translation("remus-server").charset()
            if charset:
                xsltfile = xsltfile.replace('encoding="US-ASCII"',
                                            'encoding="%s"' % charset)

        style = libxml2.readDoc(xsltfile, self.xsltfile, None, 0)
        stylesheet = libxslt.parseStylesheetDoc(style)
        if stylesheet == None:
            style.freeDoc()
            self.file = None
            logger.error("XSLT processing error")
            return

        xmlfile.seek(0)
        doc = libxml2.parseDoc(xmlfile.read())
        res = stylesheet.applyStylesheet(doc, params)
        result = stylesheet.saveResultToString(res)

        # Postprocess HTML pages, so IE6 is happy (#&¤%/&%#¤)
        if result.find('PUBLIC "-//W3C//DTD XHTML 1.0') != -1:
            # Remove the XML header
            result = '\n'.join(result.split('\n')[1:])

            # Remove CDATA markers
            result = result.replace("<![CDATA[", "").replace("]]>", "")


        self.file = StringIO(result)
        style.freeDoc()
        doc.freeDoc()

    def content_type(self):
        try:
            mime_file = os.path.splitext(self.xsltfile)[0] + '.mime'
            return file(mime_file).read().strip()
        except IOError:
            return "text/xml"

    def isdir(self):
        return False

    def open(self, mode, request=None):
        logger.info("open called")
        # Check query parameters for custom ordering
        if request.args.has_key('order'):
            # Find out what order parameters we had before, which
            # doesn't have a DESC modifier on them. For those, we
            # reverse the search order (i.e. apply the DESC modifier).
            coll_order = self.order_by or ()
            old_order = [ type(i) in types.StringTypes and i or i.name
                          for i in coll_order ]
            old_order = [ x.strip() for x in old_order \
                          if x.find("DESC") == -1 ]
            
            self.order_by = [ key in old_order and key+" DESC" or key \
                              for key in request.args['order'] ]
            self.file = None

        if not self.file or self.file.closed:
            self.create_file(request)
        #self.file.seek(0)
        file = self.file
        self.file = None
        return file
        
    def stat(self, request=None):
        if not self.file or self.file.closed:
            self.create_file(request)
        st = super(IndexXMLBase, self).stat()
        if st:
            st = list(st)
            pos = self.file.tell()
            self.file.seek(0, 2)
            st[stat.ST_SIZE] = self.file.tell()
            self.file.seek(pos)
            st = tuple(st)

        return st

def xml_fix_string(s):
    import codecs
    enc = codecs.getencoder("utf-8")
    dec = codecs.getdecoder("iso8859-1")
    return enc(dec(s.replace("&", "&amp;"))[0])[0]


def TIME_TO_SEC(*args):
    return sqlquery.Function("TIME_TO_SEC", *args)


class IndexXMLAudioList(IndexXMLBase):
    
    fields = (
        db_audiostore.remus_audio_objects.au_id,
        db_audiostore.remus_artists.art_name,
        db_audiostore.remus_albums.alb_name,
        db_audiostore.remus_art_alb_map.artalb_id,        
        db_audiostore.remus_audio_objects.au_title,
        db_audiostore.remus_audio_objects.au_length,
        db_audiostore.remus_audio_objects.au_track_number,
        db_audiostore.remus_audio_objects.au_content_type,
        db_audiostore.remus_audio_objects.au_bitrate,
        db_audiostore.remus_audio_objects.au_sample_freq,
        db_audiostore.remus_audio_objects.au_audio_mode,
        db_audiostore.remus_audio_objects.au_subtype,
        db_audiostore.remus_audio_objects.au_audio_clip,
        TIME_TO_SEC(db_audiostore.remus_audio_objects.au_length),
        )
    
    order_by = (
        db_audiostore.remus_artists.art_sortname,
        db_audiostore.remus_albums.alb_name,
        db_audiostore.remus_audio_objects.au_track_number,
        )

    document_type = "audiolist"

    def write_body(self, file):
        for dict in self.cursor:
            dict["art_name"] = xml_fix_string(dict["art_name"])
            dict["au_title"] = xml_fix_string(dict["au_title"])
            dict["alb_name"] = xml_fix_string(dict["alb_name"])
            dict["songid"] = "--song--%s" % dict["au_id"]

            filename = mk_filename(dict["songid"])
            dict["filename"] = xml_fix_string(filename)
            dict["au_length_sec"] = dict["TIME_TO_SEC(remus_audio_objects.au_length)"]

            print >> file, '''<audioclip>
            <artist>%(art_name)s</artist>
            <title>%(au_title)s</title>
            <album>%(alb_name)s</album>
            <length>%(au_length)s</length>
            <length-in-sec>%(au_length_sec)s</length-in-sec>
            <track-number>%(au_track_number)s</track-number>
            <mime>%(au_content_type)s</mime>
            <filename>%(filename)s</filename>
            <bitrate>%(au_bitrate)s</bitrate>
            <sample-freq>%(au_sample_freq)s</sample-freq>
            <audio-mode>%(au_audio_mode)s</audio-mode>
            <subtype>%(au_subtype)s</subtype>
            </audioclip>\n''' % dict
            

class IndexXMLDirList(IndexXMLBase):

    column_map = {
        'art_name' : 'Artist',
        'alb_name' : 'Album',
        'ge_genre' : 'Genre',
        'au_title' : 'Song',
        }

    link_cols = {
        'ge_genre' : "val + '/'",
        'art_name' : "val + '/'",
        'alb_name' : "val + '/list/' + " \
                     "os.path.splitext(os.path.basename(self.xsltfile))[0]",
        }

    document_type = "dirlisting"

    def __init__(self, parent, xsltfile):
        super(IndexXMLDirList, self).__init__(parent, xsltfile)

        # Inherit fields from the last constraining parent (my
        # immediate parent is the DirlistColl, which does not contain
        # any fields).
        
        self.fields = parent.parent.fields
        self.group_by = parent.parent.group_by

    def write_body(self, file):

        first_item = True
        for dict in self.cursor:

            # 'dict' might contain multiple values, but should contain
            # one and only one string value, and this is our name for
            # the subcollection
            subcol = [ v for v in dict.values()
                       if type(v) in types.StringTypes ]
            assert len(subcol) == 1
            coll = self.parent.parent.subcollection(subcol[0])

            cnt = coll.select()

            for key in dict.keys():
                if key[:11] == 'TIME_TO_SEC':
                    dict["au_length"] = dict[key]
                    del dict[key]
                elif key == "au_id":
                    dict["songid"] = "--song--%s" % dict["au_id"]
                    filename = mk_filename(dict["songid"])
                    dict["filename"] = xml_fix_string(filename)
                    del dict[key]
                elif type(dict[key]) in types.StringTypes:
                    dict[key] = xml_fix_string(dict[key])
                else:
                    del dict[key]

            # Write a list of columns first
            if first_item:
                print >> file, '  <columns cols="%s">\n' % len(dict)
                for key in dict.keys():
                    col = self.column_map.get(key)
                    print >> file, '    <column key="%s">%s</column>\n' % (key, col)
                print >> file, "  </columns>\n"
                first_item = False

            print >> file, '  <item length="%s">\n' % cnt
            for key, val in dict.items():
                if key in self.link_cols.keys():
                    linkattr = ' link="%s"' % eval(self.link_cols[key])
                else:
                    linkattr = ''
                attrs = linkattr
                print >> file, "    <%s%s>%s</%s>\n" % (key, attrs, val, key)
            
            print >> file, "  </item>\n"


class ArtistsColl(Collection):

    fields = (
        db_audiostore.remus_artists.art_name,
        )

    order_by = (
        db_audiostore.remus_artists.art_sortname,
        )

    def __init__(self, parent, query=None):
        Collection.__init__(self, parent, query)

    def isdir(self):
        return True
    
    def name(self):
        return "artist"

    def subcollection(self, name):
        coll = Collection.subcollection(self, name)
        if coll:
            return coll
        else:
            return ArtistColl(self, name)
        

class ArtistColl(Collection):

    fields = (
        db_audiostore.remus_albums.alb_name,
        db_audiostore.remus_art_alb_map.artalb_id,
        )

    group_by = (
        db_audiostore.remus_albums.alb_name,
        )

    def __init__(self, parent, artist, query=None):
        self.artist = artist
        my_query = EQUAL(db_audiostore.remus_artists_art_name, artist)
        if query:
            my_query = AND(query, my_query)
            
        Collection.__init__(self, parent, my_query)

    def isdir(self):
        return True

    def name(self):
        return self.artist

    def subcollection(self, name):
        coll = Collection.subcollection(self, name)
        if coll:
            return coll
        else:
            return AlbumColl(self, name)


class AlbumsColl(Collection):

    fields = (
        db_audiostore.remus_albums.alb_name,
        db_audiostore.remus_art_alb_map.artalb_id,
        )

    order_by = (
        db_audiostore.remus_albums.alb_name,
        )

    def __init__(self, parent, query=None):
        Collection.__init__(self, parent, query)

    def isdir(self):
        return True

    def name(self):
        return "album"

    def subcollection(self, name):
        coll = Collection.subcollection(self, name)
        if coll:
            return coll
        else:
            return AlbumColl(self, name)


class AlbumColl(Collection):

    fields = (
        db_audiostore.remus_audio_objects_au_title,
        )

    order_by = (
        db_audiostore.remus_audio_objects_au_track_number,
        )

    def __init__(self, parent, album):
        self.album = album
        my_query = EQUAL(db_audiostore.remus_albums_alb_name, album)
        if parent.query:
            my_query = AND(parent.query, my_query)
        Collection.__init__(self, parent, my_query)

    def name(self):
        return self.album

    def _rename(self, newname, coll):
        coll["album"] = newname
        
    def isdir(self):
        return True

    def subcollection(self, name):
        coll = Collection.subcollection(self, name)
        if coll:
            return coll
        else:
            return Song(self, name)


class GenreColl(Collection):

    fields = (
        db_audiostore.remus_artists_art_name,
        )

    group_by = (
        'art_name',
        )

    def __init__(self, parent, genre):
        self.genre = genre
        query = AND(
            EQUAL(db_audiostore.remus_genres_ge_genre, genre),
            EQUAL(db_audiostore.remus_audio_objects_au_artalb,
                  db_audiostore.remus_art_alb_map.artalb_id))
        Collection.__init__(self, parent, query)

    def isdir(self):
        return True

    def name(self):
        return self.genre

#    def _rename(self, newname, coll):
#        # Look up 'newname' in the DB, and update the genre reference
#        # rather than changing the name of the particular genre
#        coll["genre_id"] = newgenre
        
    def subcollection(self, name):
        subcoll = Collection.subcollection(self, name)
        if subcoll:
            return subcoll
        elif name == "songs":
            return self.songs()
        else:
            return self.artist(name)

    def artist(self, artist):
        return ArtistColl(self, artist=artist, query=self.query)


class RootColl(Collection):

    fields = (
        db_audiostore.remus_genres_ge_genre,
        )

    order_by = (
        db_audiostore.remus_genres_ge_genre,
        )



    def __init__(self, store):
        Collection.__init__(self, store=store)

    def isdir(self):
        return True

    def name(self):
        return "/"
    
    def subcollection(self, name):
        if not name:
            return self
        subcoll = Collection.subcollection(self, name)
        if subcoll:
            return subcoll
        elif name == "artist":
            return self.artists()
        elif name == "album":
            return self.albums()
        else:
            return self.genre(name)

    def genre(self, genre):
        return GenreColl(self, genre=genre)

    def artists(self):
        return ArtistsColl(self)

    def albums(self):
        return AlbumsColl(self)

    def stat(self, request=None):
        # We always exist, empty or not
        return (0444, 0, 1, 1, os.getuid(), os.getgid(), 0,
                time.time(), time.time(), time.time())
        

class AudioSaver:
    """Save an incomming stream to file.

    Tries to determine the file type using the 'file(1)' command.
    """

    def __init__(self, node):
        self.__node = node
        self.store = node.store
        self.__mime = None
        self.__len = 0
        self.__file = None
        
    def mime_type(self, data):
        from popen2 import popen2
        r, w = popen2('file -bi -')
        w.write(data)
        w.close()
        return r.read().strip()

    def __open(self, data):
        self.__mime = self.mime_type(data)
        if not self.__mime:
            logger.error("%s has no recognizable audio mime type",
                         self.__node.name())
            raise IOError, "Unknown audio format"

        if not os.path.isdir("/var/db/audiostore"):
            os.mkdir("/var/db/audiostore")

        self.__filename = os.tempnam("/var/db/audiostore", "audio.")

        # Try create file with proper file extension
        import mimetypes
        ext = mimetypes.guess_extension(self.__mime)
        if ext:
            self.__filename += ext

        self.__file = open(self.__filename, "w+")


    def write(self, data):
        if not self.__file:
            self.__open(data)

        self.__len += len(data)
        self.__file.write(data)


    def close(self):
        logger.info("Transfer of %s complete, inserting into database", self.__node.name())
        self.__file.close()
        try:
            self.store.add(
                mimetype=self.__mime,
                filename=self.__filename)

            # Allow nodes to resync, I've written to the database
            # self.__node.resync_tree()
        except IOError:
            logger.exception("Failed to add %s to the audiostore", self.__node.name())
            os.unlink(self.__filename)
            raise




import audiostore
