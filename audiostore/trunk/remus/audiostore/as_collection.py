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

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

import remus.database

import db_audiostore
from query import *

logger = logging.getLogger("audiostore.mysql")

"""
/
    artist/
        <artist>/
            <album>/
                <song>
    album/
        <album>/
            <song>
    song/
        <song>
    <genre>/
        <artist>/
        album/
        song/

    search/<text>
"""


_fs_root = None

def audiostore_file_root(root):
    """Path in the file system where audiostore files can be found, such
    as the xslt transformation script and others."""
    global _fs_root
    _fs_root = root


class Collection(object):

    tables = ()
    group_by = None
    order_by = None

    field_map = {
        'song'    : db_audiostore.au_title,
        'artist'  : db_audiostore.art_name,
        'album'   : db_audiostore.alb_name,
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

        return self.cursor.rowcount > 1

    def content_type(self):
        return "text/html"

    def open(self, mode):
        assert False

    def stat(self):
        return (0444, 0, 1, 1, os.getuid(), os.getgid(), 0,
                time.time(), time.time(), time.time())

    def filesystem(self):
        return self.fs

    def subcollection(self, name):
        if name == "songs":
            return SongsColl(self)
        elif name == "search":
            return SearchColl(self)
        elif name == "list":
            return PlaylistColl(self)
        elif name.startswith("**song**"):
            return SongId(self, name)
        else:
            return None

    def songs(self):
        """Return AudioObjects for all matching songs"""
        songs = Playlist(self)
        songs.select(fields=[db_audiostore.au_id])
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

    def select(self, fields = None):
        if not fields:
            fields = self.fields

        selection = remus.database.Select()
        for field in fields:
            selection.addcolumn(field)

        logger.info(self.query and self.query.expr()[0])
        sql, args = selection.select(self.query)
        logger.info("Performing SQL: %s", sql % self.db.literal(args))

        from MySQLdb.cursors import DictCursor
        self.cursor = self.db.cursor(DictCursor)
        return self.cursor.execute(sql, args)


    def update(self):

        selection = remus.database.Select()
        selection.addcolumn(db_audiostore.au_audio_clip)
        selection.addcolumn(db_audiostore.au_content_type)

        # Get the list of file names, and update the audio file
        # before updating the database
        cursor = self.db.cursor()
        sql, args = selection.select(query=self.query)
        count = cursor.execute(sql, args)

        for filename, mimetype in cursor:
            print "Updating", filename
            mime_map[mimetype].update(filename, self.updates)

        # Update the database
        set = [ "%s = %s" % (self.field_map[key], self.db.literal(value))
                for key, value in self.updates.items() ]
        sql = "UPDATE %s SET %s WHERE %s" % \
              (", ".join(selection.tables(self.query)),
               ", ".join(set),
               selection.where(query))

        if args:
            count = cursor.execute(sql, args)
        else:
            count = cursor.execute(sql)

        return count

    def remove(self, limit="LIMIT 1"):
        selection = remus.database.Select()
        selection.addcolumn(db_audiostore.au_id)

        sql, args = selection.select(query)
        sql += limit

        cursor = self.db.cursor()

        count = cursor.execute(sql, args)
    
        for au_id in cursor:
            audioobject = AudiostoreAudioObject(self.store, au_id)
            logger.info("removing audio clip %s", au_id)
            audioobject.remove()


class SearchColl(Collection):

    fields = (
        db_audiostore.au_title,
        db_audiostore.alb_name,
        db_audiostore.art_name,
        db_audiostore.au_length
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
                my_queries.append(REGEXP(self.field_map[field], regex))
            except ValueError:
                my_queries.append(
                    AND(REGEXP(db_audiostore.au_title, regex),
                        REGEXP(db_audiostore.alb_name, regex),
                        REGEXP(db_audiostore.art_name, regex)))
        return reduce(AND, my_queries)


class SongsColl(Collection):

    fields = (
        db_audiostore.au_title,
        db_audiostore.au_length
        )

    def __init__(self, parent):
        Collection.__init__(self, parent, parent.query)

    def name(self):
        return "songs"


class Song(Collection):

    # Not really a collection, this is a single song
    fields = (
        db_audiostore.au_title,
        db_audiostore.au_length
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
        count = self.select(fields=(db_audiostore.au_audio_clip,))
        if count != 1:
            raise IOError, "file not found"

        return os.stat(self.cursor.fetchone()["au_audio_clip"])

    def content_type(self):
        count = self.select(fields=(db_audiostore.au_content_type,))
        if count != 1:
            raise IOError, "file not found"

        return self.cursor.fetchone()["au_content_type"]

    def open(self, mode):
        if mode and mode[0] == 'w':
            # Someone is saving a file!
            return AudioSaver(self, self.dbconnection())
        else:
            # Open the audio file, and return file object here
            count = self.select(fields=(db_audiostore.au_audio_clip,))
            if count != 1:
                raise IOError, "file not found"
            
            filename = self.cursor.fetchone()["au_audio_clip"]
            return open(filename)


class SongId(Song):

    def __init__(self, parent, songid):
        self.id = songid[8:]
        query = EQUAL(db_audiostore.au_id, self.id)
        Collection.__init__(self, parent, query)

    def name(self):
        return "__song__%s" % self.id


class SongList(Collection):

    fields = (
        db_audiostore.au_id,
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
        print "FS root is", _fs_root
        xsl_stylesheet = os.path.join(_fs_root, "styles", "%s.xsl" % name)
        return IndexXML(self, xsl_stylesheet)


def xml_fix_string(s):
    import codecs
    enc = codecs.getencoder("utf-8")
    dec = codecs.getdecoder("iso8859-1")
    return enc(dec(s.replace("&", "&amp;"))[0])[0]


class TIME_TO_SEC:
    def __init__(self, field):
        self.name = "TIME_TO_SEC(%s)" % field.name
        self.table = field.table

class IndexXML(Collection):
    
    fields = (
        db_audiostore.au_id,
        db_audiostore.art_name,
        db_audiostore.alb_name,
        db_audiostore.au_title,
        db_audiostore.au_length,
        db_audiostore.au_track_number,
        db_audiostore.au_content_type,
        db_audiostore.au_bitrate,
        db_audiostore.au_sample_freq,
        db_audiostore.au_audio_mode,
        db_audiostore.au_subtype,
        db_audiostore.au_audio_clip,
        TIME_TO_SEC(db_audiostore.au_length),
        )
    
    order_by = (
        "au_name",
        "alb_name",
        "au_track_number",
        )
    
    def __init__(self, parent, xsltfile):
        super(IndexXML, self).__init__(parent)
        self.urlroot = "/"
        self.file = None
        self.server_name = 'unknown.org'
        self.xsltfile = xsltfile

    def create_file(self):
        # Build an index page
        import tempfile
        fd, tempname = tempfile.mkstemp()
        cnt = self.select()
        os.write(fd, '<?xml version="1.0" encoding="utf-8"?>\n')
        os.write(fd, '<audiolist length="%s">\n' % cnt)

        os.write(fd, '\t<path>%s</path>\n' % xml_fix_string(self.parent.cwd()))

        for dict in self.cursor:
            
            dict["art_name"] = xml_fix_string(dict["art_name"])
            dict["au_title"] = xml_fix_string(dict["au_title"])
            dict["alb_name"] = xml_fix_string(dict["alb_name"])
            dict["songid"] = "**song**%s" % dict["au_id"]

            filename = self.filesystem().mk_filename(dict["songid"])
            dict["filename"] = xml_fix_string(filename)
            dict["au_length_sec"] = dict["TIME_TO_SEC(au_length)"]

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

    def open(self, mode):
        if not self.file or self.file.closed:
            self.create_file()
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
        db_audiostore.art_name,
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
        db_audiostore.alb_name,
        )

    group_by = (
        'alb_name',
        )

    def __init__(self, parent, artist, query=None):
        self.artist = artist
        my_query = EQUAL(db_audiostore.art_name, artist)
        if query:
            my_query = AND(query, my_query)
            
        Collection.__init__(self, parent, my_query)

    def isdir(self):
        return True

    def name(self):
        return self.artist

    def subcollection(self, name):
        print "Artist: subcollection =", name
        coll = Collection.subcollection(self, name)
        if coll:
            return coll
        else:
            return AlbumColl(self, name)


class AlbumsColl(Collection):

    fields = (
        db_audiostore.alb_name,
        )

    def __init__(self, parent, query=None,):
        Collection.__init__(self, parent, query)

    def isdir(self):
        return True

    def name(self):
        return "album"


class AlbumColl(Collection):

    fields = (
        db_audiostore.au_title,
        )

    order_by = (
        'au_track_number',
        )

    def __init__(self, parent, album):
        self.album = album
        Collection.__init__(self, parent, AND(parent.query,
                                              EQUAL(db_audiostore.alb_name,
                                                    album)))

    def name(self):
        return self.album

    def isdir(self):
        return True

    def subcollection(self, name):
        print "Album: subcollection =", name
        coll = Collection.subcollection(self, name)
        if coll:
            return coll
        else:
            return Song(self, name)


class GenreColl(Collection):

    fields = (
        db_audiostore.art_name,
        )

    group_by = (
        'art_name',
        )

    def __init__(self, parent, genre):
        self.genre = genre
        query = EQUAL(db_audiostore.ge_genre, genre)
        Collection.__init__(self, parent, query)

    def isdir(self):
        return True

    def name(self):
        return self.genre

    def subcollection(self, name):
        print "Genre: subcollection =", name
        
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
        db_audiostore.ge_genre,
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
    
