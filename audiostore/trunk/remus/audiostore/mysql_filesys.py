"""Mapping a MySQL database to a file system.

"""

import logging
import posixpath
import stat
import os
import time
import string

logger = logging.getLogger("audiostore")

import time

class QueryCache:
    def __init__(self, size=100):
        self.__maxsize = size
        self.__map = {}

    def __setitem__(self, path, query):
        if not self.__map.has_key(path):
            self.__map[path] = [query, time.time()]
            self.__renorm()

    def __getitem__(self, path):
        item = self.__map[path]
        item[1] = time.time()
        return item[0]

    def __len__(self):
        return len(self.__map)

    def has_key(self, path):
        return self.__map.has_key(path)

    def __renorm(self):
        if len(self.__map) > self.__maxsize:
            # We've grown too big, remove half the entries
            # to avoid this routine constantly being called
            entries = self.__map.items()
            entries.sort(lambda x, y: cmp(y[1][1], x[1][1]))
            for entry in entries[self.__maxsize / 2:]:
                del self.__map[entry[0]]


class mysql_filesystem:

    # Must be the inverses of each other!
    db_to_fn = string.maketrans(" ", "_")
    fn_to_db = string.maketrans("_", " ")
    
    def __init__ (self, root_query):
        self.__root_query = root_query
        self.__cwd = root_query
        self.__cwd.fs = self
        self.__last_query = None
        self.__last_path = None
        self.__path_to_query = QueryCache()

    def build_sql_hier(self, path):
        logger.info("Number of saved queries: %d", len(self.__path_to_query))
        if path:
            if self.__path_to_query.has_key(path):
                return self.__path_to_query[path]
            else:
                pathlist = path.split("/")
                print "Path (%s), Pathlist: %s" % (path, pathlist)
                if pathlist and not pathlist[-1]:
                    pathlist = pathlist[:-1]
                if pathlist and not pathlist[0]:
                    pathlist = pathlist[1:]
                hier = self.__root_query
                for comp in pathlist:
                    hier = hier.subcollection(self.mk_sqlname(comp))
                    print hier, comp
                    hier.fs = self
        else:
            hier = self.__cwd

        self.__path_to_query[path] = hier
        return hier

    def current_directory (self):
        "Return a string representing the current directory."
        return self.__cwd.cwd()

    def listdir (self, path, long=0):
        """Return a listing of the directory at 'path' The empty string
        indicates the current directory.  If 'long' is set, instead
        return a list of (name, stat_info) tuples
        """
        hier = self.build_sql_hier(path)

        # Perform query
        hier.select()
        rows = hier.cursor.fetchall()

        # Replace None with the string "<none>"
        rows = [ [ col or "<none>" for col in row.values() ] for row in rows ]
        print rows
        rows = map(lambda t: self.mk_filename("--".join(t)), rows)
        return rows

    def open (self, path, mode, content_type=None):
        "Return an open file object"
        hier = self.build_sql_hier(path)
        try:
            return hier.open(mode)
        except:
            logger.exception("Failed to open %s", path)
            raise

    def content_type(self, path):
        return self.build_sql_hier(path).content_type()

    def stat (self, path):
        "Return the equivalent of os.stat() on the given path."
        dbstat = list(self.build_sql_hier(path).stat())
        dbstat[stat.ST_MODE] = 0444
        dbstat[stat.ST_DEV] = 0
        return tuple(dbstat)

    def isdir (self, path):
        "Does the path represent a directory?"
        return self.build_sql_hier(path).isdir()

    def isfile (self, path):
        "Does the path represent a plain file?"
        return not self.isdir(path)

    def cwd (self, path):
        "Change the working directory."
        p = self.normalize(posixpath.join(self.current_directory(), path))
        self.__cwd = self.build_sql_hier(p)

    def cdup (self):
        "Change to the parent of the current directory."
        return self.cwd("..")

    def longify (self, path):
        """Return a 'long' representation of the filename
        [for the output of the LIST command]"""
        print "Trying to longify %s" % path

    # utility methods
    def normalize (self, path):
        import re
        # watch for the ever-sneaky '/+' path element
        path = re.sub('/+', '/', path)
        p = posixpath.normpath (path)
        # remove 'dangling' cdup's.
        if len(p) > 2 and p[:3] == '/..':
            p = '/'
        return p

    def mk_filename(self, path):
        return path.replace("?", "  q").replace("/", "\\").replace("&", " and ").replace("(", " p ").replace(")", " d ").translate(self.db_to_fn).lower()

    def mk_sqlname(self, path):
        return path.translate(self.fn_to_db).replace(" d ", ")").replace(" p ", "(").replace("  and  ", " & ").replace("\\", "/").replace("  q", "?")
