"""Twisted resource for serving Remus audiostore objects.
"""

import time
import types
import urllib

import twisted.web.resource

import remus.audiostore
import webdav


# Cache of SQL queries
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


_path_to_query = QueryCache()

def get_cached_collection(path, parent, child):
    print "Number of saved queries:", len(_path_to_query)
    if _path_to_query.has_key(path):
        return _path_to_query[path]

    coll = parent.subcollection(child)
 #   _path_to_query[path] = coll
    return coll


def diffpath(path1, path2):
    import os
    t1 = path1.split(os.path.sep)
    t2 = path2.split(os.path.sep)
    count = min(len(t1), len(t2))
    i = 0
    while i < count and t1[i] == t2[i]:
        i += 1
    return t1[i:], t2[i:]


class ASWrapper(webdav.WebDAV):
    "Wraps an audiostore collection as a Twisted resource"
    
    def __init__(self, collection):
        self.collection = collection
        twisted.web.resource.Resource.__init__(self)

    def getChild(self, child, request):
        if child:
            child = remus.audiostore.mk_sqlname(child)

#            return ASWrapper(self.collection.subcollection(child))
            prepath = tuple(request.prepath) + (child, )
            ch = get_cached_collection(prepath,
                                       self.collection,
                                       child)
            if ch.stat():
                return ASWrapper(ch)
            else:
                print "Failed to stat", ch, ch.cwd()
                return twisted.web.resource.error.NoResource("No such resource")
        else:
            return self

    def listDynamicNames(self):

        # Perform query
        self.collection.select(cursorclass=None)
        rows = self.collection.cursor.fetchall()

        # Replace None with the string "<none>"
        rows = [ [ col or "<none>" for col in r ] for r in rows ]
        print rows
        rows = [ filter(lambda c: isinstance(c, types.StringTypes), r)
                 for r in rows ]
        rows = [ remus.audiostore.mk_filename("--".join(r)) for r in rows ]

        return rows

    def listDynamicEntities(self, request=None):
        names = self.listDynamicNames()
        e = [ ASWrapper(self.collection.subcollection(n)) for n in names ]
        return e

    def isdir(self):
        return self.collection.isdir()

    def isfile(self):
        return not self.isdir()
    
    def stat(self):
        return self.collection.stat()

    def moveone(self, src, dst, overwrite):
        print "Renaming %s to %s" % (src, dst)
        assert False

    def movetree(self, src, dst, overwrite):
        print "Renaming %s to %s" % (src, dst)
        
        src_path, dst_path = diffpath(src, dst)
        if len(src_path) != len(dst_path):
            raise error.DAV_Forbidden("Can't move up/down the hierarchy")

        self.collection.rename(src_path, dst_path)
        self.collection.update()

    def open(self, mode):
        return self.collection.open(mode)

    def content_type(self):
        return self.collection.content_type()

    def get_directory(self, request):
        inet, addr, port = request.getHost()
        if port == 80:
            hostport = ''
        else:
            hostport = ':%d' % port

        server =  urllib.quote('http%s://%s%s/' % (
            request.isSecure() and 's' or '',
            request.getRequestHostname(),
            hostport), "/:")

        # Generate an index.html page of this directory, by requesting
        # the generic "list" child, which generates an XML document from
        # the SQL query, then the "index.html" child, which performs
        # the XML -> html XSLT transformation. This requires the
        # index.html.xsl file to be installed, which is part of the
        # standard distribution.
        list = self.collection.subcollection("list")
        prepath = tuple(request.prepath) + ("list", "index.html")
        coll = get_cached_collection(prepath, list, "index.html")


        # Check query parameters for custom ordering
        if request.args.has_key('order'):
            # Find out what order parameters we had before, which
            # doesn't have a DESC modifier on them. For those, we
            # reverse the search order (i.e. apply the DESC modifier).
            old_order = [ x.strip() for x in coll.order_by \
                          if x.find("DESC") == -1 ]
            
            coll.order_by = [ key in old_order and key+" DESC" or key \
                              for key in request.args['order'] ]
            
        
        # Set up some information for the HTML generation
        coll.server_name = server
        coll.urlroot = "/music"

        file = coll.open("r", request)
        request.write(file.read())
        file.close()
        request.finish()

