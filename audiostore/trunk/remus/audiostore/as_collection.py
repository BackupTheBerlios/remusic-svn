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
import stat
import time
import posixpath
import string

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

import MySQLdb.cursors
import sqlquery

import db_audiostore
#from query import *

from sqlquery import AND, OR, REGEXP, EQUAL

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
        'album_id': db_audiostore.remus_audio_objects_au_album,
        'artist_id':db_audiostore.remus_albums_alb_artist,
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

    def open(self, mode):
        assert False

    def stat(self):
        if self.isdir() or self.select() > 0:
            stat = (0444, 0, 1, 1, os.getuid(), os.getgid(), 0,
                    time.time(), time.time(), time.time())
        else:
            stat = None
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

    def select(self, fields = None, cursorclass = MySQLdb.cursors.DictCursor):
        if not fields:
            fields = self.fields or self.parent.fields

        selection = sqlquery.Select()
        for field in fields:
            selection.addcolumn(field)

        sql, args = selection.select(
            query=self.query,
            order_by=self.order_by,
            group_by=self.group_by)

        logger.info("Performing SQL: %s", sql % self.db.literal(args))

        self.cursor = self.db.cursor(cursorclass)
        return self.cursor.execute(sql, args)


    def update(self):

        selection = sqlquery.Select()
        selection.addcolumn(db_audiostore.remus_audio_objects_au_audio_clip)
        selection.addcolumn(db_audiostore.remus_audio_objects_au_content_type)

        # Get the list of file names, and update the audio file
        # before updating the database
        cursor = self.db.cursor()
        sql, args = selection.select(query=self.query)
        count = cursor.execute(sql, args)

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

        sql, args = selection.select(query=self.query)
        count = cursor.execute(sql, args)

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

        sql, args = selection.select(query)
        sql += limit

        cursor = self.db.cursor()

        count = cursor.execute(sql, args)
    
        for au_id in cursor:
            audioobject = audiostore.AudioObject(self.store, au_id)
            logger.info("removing audio clip %s", au_id)
            audioobject.remove()


class SearchColl(Collection):

    fields = (
        db_audiostore.remus_audio_objects_au_title,
        db_audiostore.remus_albums_alb_name,
        db_audiostore.remus_artists_art_name,
        db_audiostore.remus_audio_objects_au_length
        )

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
                field, regex = q.split('=')
                my_queries.append(sqlquery.REGEXP(self.field_map[field], regex))
            except ValueError:
                my_queries.append(
                    OR(OR(REGEXP(db_audiostore.remus_audio_objects_au_title, q),
                          REGEXP(db_audiostore.remus_albums_alb_name, q)),
                       REGEXP(db_audiostore.remus_artists_art_name, q)))
        return reduce(AND, my_queries)


class SongsColl(Collection):

    fields = (
        db_audiostore.remus_audio_objects_au_title,
        db_audiostore.remus_audio_objects_au_length
        )

    def __init__(self, parent):
        Collection.__init__(self, parent, parent.query)

    def name(self):
        return "songs"


class Song(Collection):

    # Not really a collection, this is a single song
    fields = (
        db_audiostore.remus_audio_objects_au_title,
        db_audiostore.remus_audio_objects_au_length
        )

    def __init__(self, parent, songtitle):
        self.title = songtitle
        query = TITLE_EQ(songtitle)
        if parent.query:
            query = AND(parent.query, query)
        Collection.__init__(self, parent, query)

    def isdir(self):
        return False

    def name(self):
        return self.title

    def stat(self):
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

    def open(self, mode):
        if mode and mode[0] == 'w':
            # Someone is saving a file!
            return AudioSaver(self, self.dbconnection())
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
    

class SongList(Collection):

    fields = (
        db_audiostore.remus_audio_objects_au_id,
        )

    order_by = (
        "alb_name",
        "au_track_number",
        )

    def __init__(self, parent):
        super(SongList, self).__init__(parent)

    def name(self):
        return "songlist"

    

class PlaylistColl(Collection):
    """Return a playlist file in some format.

    A playlist is a generic term for any type of file containing a list
    of songs. Through the PlaylistColl class, specific playlist formats
    are obtained by looking for a matching XSLT stylesheet in the
    styles catalog, and applying them to a standard XML file produced
    from the query"""

    def __init__(self, parent):
        # This collection doesn't modify the parent's collection
        # in any way
        super(PlaylistColl, self).__init__(parent)

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
            return IndexXML(self, xsl_stylesheet)
        else:
            return subcol


def xml_fix_string(s):
    import codecs
    enc = codecs.getencoder("utf-8")
    dec = codecs.getdecoder("iso8859-1")
    return enc(dec(s.replace("&", "&amp;"))[0])[0]


def TIME_TO_SEC(*args):
    return sqlquery.Function("TIME_TO_SEC", *args)

class IndexXML(Collection):
    
    fields = (
        db_audiostore.remus_audio_objects_au_id,
        db_audiostore.remus_artists_art_name,
        db_audiostore.remus_albums_alb_name,
        db_audiostore.remus_audio_objects_au_title,
        db_audiostore.remus_audio_objects_au_length,
        db_audiostore.remus_audio_objects_au_track_number,
        db_audiostore.remus_audio_objects_au_content_type,
        db_audiostore.remus_audio_objects_au_bitrate,
        db_audiostore.remus_audio_objects_au_sample_freq,
        db_audiostore.remus_audio_objects_au_audio_mode,
        db_audiostore.remus_audio_objects_au_subtype,
        db_audiostore.remus_audio_objects_au_audio_clip,
        TIME_TO_SEC(db_audiostore.remus_audio_objects_au_length),
        )
    
    order_by = (
        "au_title",
        "alb_name",
        "au_track_number",
        )
    
    def __init__(self, parent, xsltfile):
        super(IndexXML, self).__init__(parent)
        self.urlroot = "/"
        self.file = None
        self.server_name = 'unknown.org'
        self.xsltfile = xsltfile

    def create_file(self, request=None):
        # Build an index page
        import tempfile
        fd, tempname = tempfile.mkstemp()
        cnt = self.select()
        os.write(fd, '<?xml version="1.0" encoding="utf-8"?>\n')
        os.write(fd, '<audiolist length="%s">\n' % cnt)

        if request:
            path = request.path[len(self.urlroot):]
        else:
            path = self.parent.cwd()
        os.write(fd, '\t<path>%s</path>\n' % xml_fix_string(path).replace("%20", ' '))

        for dict in self.cursor:
            dict["art_name"] = xml_fix_string(dict["art_name"])
            dict["au_title"] = xml_fix_string(dict["au_title"])
            dict["alb_name"] = xml_fix_string(dict["alb_name"])
            dict["songid"] = "--song--%s" % dict["au_id"]

            filename = mk_filename(dict["songid"])
            dict["filename"] = xml_fix_string(filename)
            dict["au_length_sec"] = dict["TIME_TO_SEC(remus_audio_objects.au_length)"]

            os.write(fd, '''<audioclip>
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
            </audioclip>\n''' % dict)
            
        os.write(fd, "</audiolist>\n")
        os.close(fd)
        self.cursor.close()
        self.cursor = None

        # Perform xslt transformation on the file
        from commands import getstatusoutput
        params = "--stringparam audiostore.root %s/" % self.urlroot
        params += " --stringparam audiostore.url %s%s" % (self.server_name,
                                                          self.urlroot)
        logger.info("xsltproc %s %s %s" % \
                    (params, self.xsltfile, tempname))
        st, output = getstatusoutput("xsltproc %s %s %s" % \
                                     (params, self.xsltfile, tempname))

        self.file = StringIO(output)
        os.unlink(tempname)

    def content_type(self):
        return "text/xml"

    def isdir(self):
        return False

    def open(self, mode, request=None):
        if not self.file or self.file.closed:
            self.create_file(request)
        self.file.seek(0)
        return self.file
        
    def stat(self):
        if not self.file or self.file.closed:
            self.create_file()
        st = list(super(IndexXML, self).stat())
        pos = self.file.tell()
        self.file.seek(0, 2)
        st[stat.ST_SIZE] = self.file.tell()
        self.file.seek(pos)
        return tuple(st)



class ArtistsColl(Collection):

    fields = (
        db_audiostore.remus_artists_art_name,
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
        db_audiostore.remus_albums_alb_name,
        )

    group_by = (
        'alb_name',
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
        db_audiostore.remus_albums_alb_name,
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
        'au_track_number',
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
            EQUAL(db_audiostore.art_id, db_audiostore.remus_audio_objects_au_artist))
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
    
import audiostore
