"""Maps requests for audio resources to RDF queries.


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

import remus.audiostore.storage
from remus.audiostore.storage import rdf, rem, dc

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
    """Base class for 'collections'.

    A collection corresponds to a folder/directory or a single file in
    a file system.
    """

    def __init__(self, parent=None, store=None):
        self.parent = parent
        if store is None:
            self.store = parent.store
        else:
            self.store = store


    def isdir(self):
        """Is this a 'directory' rather than a 'file' resource?"""
        # Default is yes
        return True


    def stat(self, request=None):
        """Corresponds to os.stat.

        This class hierarchy is accessed by a WebDAV server, so we're
        faking a 'file system' by implementing some normal file system calls.

        The default implementation is to return results indicating
        this resource exists. Subclasses may raise IOError to indicate
        nonexistance.
        """
        return os.stat_result([0555, 0, 1, 1, os.getuid(), os.getgid(), 0,
                               time.time(), time.time(), time.time()])


    def subcollection(self, name):
        """Return a subcollection for this collection.

        This method is used to traverse the storage using URL path
        traversal.

        Every collection supports the following subcollections:

        - 'songs', list of all songs matching the scope of this
           collection

        - 'search', seach the songs using a pattern

        - 'list', list of all songs mapped to a specific output
          format. Format is selected by subcollections of the 'list'
          collection.

        - 'dirlist', list of all subcollections in a specific output
          format. Format is selected by subcollections of the
          'dirlist' collection.

        - <song identifier>, returns a specific song
        """
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


class QueryCollection(Collection):
    element_name = "%s"
    distinct = True

    def __init__(self, parent=None, store=None, query=None):
        Collection.__init__(self, parent, store)
        self.query = query or (parent and parent.query) or ()
        if parent:
            self.select = parent.select + self.select + self.query

    def stat(self, request=None):
        """Perform query to determine if this resource exists."""
        if self.search() > 0:
            stat = os.stat_result([0444, 0, 1, 1, os.getuid(), os.getgid(), 0,
                                   time.time(), time.time(), time.time()])
        else:
            raise IOError, "file not found"

        if self.cursor:
            self.cursor.close()
            self.cursor = None
        return stat


    def rdfquery(self):
        """Query the storage for matching resources
        """
        fields = self.fields or self.parent.fields
        query = remus.audiostore.storage.sparql_query(fields, self.select,
                                                      self.distinct)
        return query.execute(self.store)


    def search(self):

        result = self.rdfquery()

        keys = []
        def in_result(node, keys):
            n = node.get(self.key_field, None)
            if n and str(n) in keys:
                return True
            else:
                keys.append(str(n))
                return False

        return [ self.element_name % res for res in result
                 if not in_result(res, keys) ]


class Root(Collection):

    __subcollections = {
        'artists': Artists,
        'albums' : Albums,
        'genres' : Genres,
        'tracks' : Tracks,
        }

    def __init__(self, store):
        Collection.__init__(self, store=store)


    def stat(self, request=None):
        # We always exist, empty or not
        return (0555, 0, 1, 1, os.getuid(), os.getgid(), 0,
                time.time(), time.time(), time.time())


    def subcollection(self, name):
        """Return a subcollection of the root element."""
        if not name:
            return self
        subcoll = Collection.subcollection(self, name)
        if subcoll:
            return subcoll
        elif self.__subcollections.has_key(name):
            return self.__subcollections[name](self)
        else:
            raise IOError("File not found")


class Genres(Collection):

    element_name = "%(album)s"
    key_field = 'albumid'
    fields = ['album', 'albumid']
    select = (
        ("?track",   "mq:album", "?albumid"),
        ("?albumid", "rdf:type", "mm:Album"),
        ("?albumid", "dc:title", "?album"),
        )
    
    def __init__(self, parent, genre):
        self.genre = genre
        self.select = self.select + (
            ("?track", "remus:genre", "'%s'" % genre),
            )
        Collection.__init__(self, parent)


    def subcollection(self, name):
        """Return a subcollection of the root element.

        Valid subcollections are all the standard subcollections, plus
        the following:

        - 'artist'
        - 'album'
        - a genre name
        """
        if not name:
            return self
        subcoll = Collection.subcollection(self, name)
        if subcoll:
            return subcoll
        elif name == "songs":
            return Songs(self)
        else:
            return Artists(self, name)


class Artists(Collection):
    element_name = "%(artist)s"
    key_field = 'artistid'
    fields = ['artist', 'artistid']
    select = (
        ("?artistid", "rdf:type", "mm:Artist"),
        ("?artistid", "dc:title", "?artist"),
        )
    
    def subcollection(self, name):
        coll = Collection.subcollection(self, name)
        if coll:
            return coll
        else:
            return Albums(self, query=(
                ("?albumid", "dc:creator", "?artistid"),
                ("?artistid", "dc:title", "'%s'" % name),
                ))


class Artist(Collection):

    def subcollection(self, name):
        coll = Collection.subcollection(self, name)
        if coll:
            return coll
        else:
            return Album(self, query=(("?albumid", "dc:creator", "?artistid"),))


class Albums(Collection):
    element_name = "%(album)s"
    key_field = 'albumid'
    fields = ['album', 'albumid']
    select = (
        ("?track",   "mq:album", "?albumid"),
        ("?albumid", "dc:title", "?album"),
        )
    
    def __init__(self, parent, query=None):
        Collection.__init__(self, parent, query=query)

    def subcollection(self, name):
        coll = Collection.subcollection(self, name)
        if coll:
            return coll
        else:
            return Album(self, name)


class Album(Collection):
    element_name = "%(track)s"
    key_field = 'trackid'
    fields = ['track', 'trackid', 'file']
    select = (
        ("?trackid",   "dc:title", "?track"),
        ("?trackid", "rdf:type", "mm:Track"),
        )

    def __init__(self, parent, name):
        self.name = name
        self.select = self.select + (
            ("?track",   "mq:album", "?albumid"),
            ("?albumid", "dc:title", "''" % name),
            )
            
        Collection.__init__(self, parent)
        

class Songs(Collection):
    
    element_name = "%(track)s"
    key_field = 'trackid'
    fields = ['track', 'trackid', 'file']
    select = (
        ("?trackid",   "dc:title", "?track"),
        ("?trackid", "rdf:type", "mm:Track"),
        )
    
    def __init__(self, parent):
        Collection.__init__(self, parent)
