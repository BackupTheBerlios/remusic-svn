# -*- Mode: Python -*-
#
#       Author: Daniel Larsson <Daniel.Larsson@servicefactory.se>
#       Copyright 2003 by Daniel Larsson
#                                                All Rights Reserved.
#

# standard python modules
import mimetypes
import re
import stat
import time
import string
import os
import types
import logging
import posixpath

# medusa modules
import medusa.http_date
import medusa.http_server
import medusa.status_handler
import medusa.producers

from medusa.script_handler import collector
from medusa.put_handler import put_collector

# local modules
import propfind
import errors
import constants

unquote = medusa.http_server.unquote

logger = logging.getLogger("medusa.webdav")

# This is a WebDAV handler.  It implements a subset of the WebDAV
# protocol, and delivers files using a 'filesystem' object, which
# is an abstraction present in the medusa distribution.
#


from medusa.counter import counter

class webdav_handler:

    valid_commands = ['GET', 'HEAD', 'PUT', 'OPTIONS',
                      'PROPFIND', 'PROPPATCH', 'MKCOL']

    IDENT = 'WebDAV HTTP Request Handler'

    # Properties

    PROPS={"DAV:" : ('creationdate', 
                     'displayname', 
                     'getcontentlanguage', 
                     'getcontentlength', 
                     'getcontenttype', 
                     'getetag', 
                     'getlastmodified', 
                     'lockdiscovery', 
                     'resourcetype', 
                     'source', 
                     'supportedlock'),
           "NS2" : ("p1","p2")
           }


    # here we define which methods handle which namespace
    # the first item is the namespace URI and the second one
    # the method prefix
    # e.g. for DAV:getcontenttype we call dav_getcontenttype()
    M_NS={"DAV:" : "_get_dav",
          "NS2"  : "ns2" }


    # Pathnames that are tried when a URI resolves to a directory name
    directory_defaults = [
            'index.html',
            'default.html'
            ]

    default_file_producer = medusa.producers.file_producer

    def __init__ (self, filesystem, urlroot):
        self.filesystem = filesystem
        self.urlroot = urlroot

        # count total hits
        self.hit_counter = counter()
        # count file deliveries
        self.file_counter = counter()
        # count cache hits
        self.cache_counter = counter()

    def __repr__ (self):
        return '<%s (%s hits) at %x>' % (
                self.IDENT,
                self.hit_counter,
                id (self)
                )

    def match (self, request):
        return request.uri[:len(self.urlroot)] == self.urlroot


    def handle_request (self, request):

        if request.command not in self.valid_commands:
            request.error (400) # bad request
            return

        logger.info("Incomming %s request for %s",
                    request.command, request.uri)

        self.hit_counter.increment()

        mname = 'do_' + request.command
        if not hasattr(self, mname):
            request.error(501)
            return
        method = getattr(self, mname)
        method(request)


    def continue_request (self, request, input_data):
        mname = 'cont_' + request.command
        if not hasattr(self, mname):
            request.error(501)
            return
        method = getattr(self, mname)
        method(request, input_data)


    def do_OPTIONS(self, request):
        request["Allow"] = ", ".join(self.valid_commands)
        request["Content-Type"] = "text/plain"
        request["DAV"] = "1"
        request.done()


    def do_PROPFIND(self, request):
        len = int(request.get_header("Content-Length"))
        if len:
            collector(self, len, request)
        else:
            self.cont_PROPFIND(request, None)


    def cont_PROPFIND(self, request, stdin):
        self.request = request

        depth = request.get_header('Depth')
        if not depth:
            depth = 'infinity'

        path, params, query, fragment = request.split_uri()

        if '%' in path:
            path = unquote (path)

        #path = path[len(self.urlroot):]
        try:
            self.filesystem.stat(path[len(self.urlroot):])
        except IOError:
            # logger.exception("Failed to stat %s", path)
            request.error(404)
            return

        propf = propfind.PROPFIND(path, self, depth)

        if stdin:
            propf.read_propfind(stdin.read())

        try:
            data = propf.createResponse() + '\n'
            logger.info("PROPFIND response: %s", data)
        except errors.DAV_Error, (errorcode, dd):
            request.error(errorcode)
            return

        request['Transfer-Encoding'] = "chunked"
        request.push(medusa.producers.chunked_producer(
            medusa.producers.simple_producer(data)))
        request.response(207)
        request.done()


    def do_GET(self, request):
        path, params, query, fragment = request.split_uri()

        if '%' in path:
            path = unquote (path)

        path = path[len(self.urlroot):]

        # strip off all leading slashes
        while path and path[0] == '/':
            path = path[1:]

        if self.filesystem.isdir (path):
            if path and path[-1] != '/':
                server = request.channel.server.server_name
                if request.channel.server.port != 80:
                    server += ":%d" % request.channel.server.port
                request['Location'] = 'http://%s%s/' % (
                        server,
                        posixpath.join(self.urlroot, path)
                        )
                request.error (301)
                return


            # GET done on a directory. Defer to subclasses what
            # to do in this case. If get_directory haven't generated
            # a response, the returned path is supposed to be a valid
            # file to read the data from. One common implementation
            # is to search for files such as 'index.html', and return
            # the contents of this, when a directory path is found in
            # the URI. In such cases, all get_directory needs to do is
            # to verify the file exists, and if so, return the path to
            # it.
            path = self.get_directory(request)

            # If the request has been responded to, the request's channel
            # doesn't point back to the request anymore
            if request.channel.current_request != request:
                return

        elif not self.filesystem.isfile (path):
            request.error (404) # Not Found
            return

        file_length = self.filesystem.stat (path)[stat.ST_SIZE]

        ims = get_header_match (IF_MODIFIED_SINCE, request.header)

        length_match = 1
        if ims:
            length = ims.group (4)
            if length:
                try:
                    length = string.atoi (length)
                    if length != file_length:
                        length_match = 0
                except:
                    pass

        ims_date = 0

        if ims:
            ims_date = medusa.http_date.parse_http_date (ims.group (1))

        try:
            mtime = self.filesystem.stat (path)[stat.ST_MTIME]
        except:
            request.error (404)
            return

        if length_match and ims_date:
            if mtime <= ims_date:
                request.reply_code = 304
                request.done()
                self.cache_counter.increment()
                return
        try:
            file = self.filesystem.open (path, 'rb')
        except IOError:
            request.error (404)
            return

        request['Last-Modified'] = medusa.http_date.build_http_date (mtime)
        request['Content-Length'] = file_length
        self.set_content_type (path, request)

        if request.command == 'GET':
            request.push (self.default_file_producer (file))

        self.file_counter.increment()
        request.done()


    do_HEAD = do_GET


    def do_MKCOL(self, request):
        path, params, query, fragment = request.split_uri()

        if '%' in path:
            path = unquote (path)

        path = path[len(self.urlroot):]

        # test if file already exists
        try:
            self.filesystem.stat(path)
            request.error(405)
            return
        except:
            pass

        # test if parent exists
        h,t=os.path.split(path[:-1])
        try:
            self.filesystem.stat(h)
        except:
            request.error(409)
            return

        try:
            self.filesystem.mkdir(path)
            request.reply_now(200)
        except:
            request.error(403)


    def do_DELETE(self, request):
        request.error(403)


    def do_PUT(self, request):
        try:
            l = int(request.get_header("Content-Length"))
            logger.info("Incomming file: %d bytes long", l)

            path, params, query, fragment = request.split_uri()


            if '%' in path:
                path = unquote (path)

                path = path[len(self.urlroot):]

            if request.has_key("Content-Type"):
                content_type = request["Content-Type"]

            try:
                file = self.filesystem.open(path, 'w+')
                request.collector = put_collector(file, l, request, 0)

                # no terminator while receiving PUT data
                request.channel.set_terminator (None)
            except:
                request.error(424)
        except:
            request.error(411)


    def get_directory(self, request):
        """When trying to GET a directory, this method is called, to allow
        subclasses to redefine behaviour.

        The default behaviour is to look for files with the names contained
        in the self.directory_defaults list, and return the first such file
        found."""
        path = request.split_uri()[0]

        found = 0
        if path and path[-1] != '/':
            path = path + '/'
        for default in self.directory_defaults:
            p = path + default
            if self.filesystem.isfile (p):
                path = p
                found = 1
                break
        if not found:
            request.error (404) # Not Found

        return path
        


    def set_content_type (self, path, request):
        try:
            request['Content-Type'] = self.filesystem.content_type(path)
            return
        except AttributeError:
            pass
        
        ext = get_extension (path).lower()
        typ, encoding = mimetypes.guess_type(path)
        if typ is not None:
            request['Content-Type'] = typ
        else:
            # TODO: test a chunk off the front of the file for 8-bit
            # characters, and use application/octet-stream instead.
            request['Content-Type'] = 'text/plain'

    def status (self):
        return medusa.producers.simple_producer (
                '<li>%s' % medusa.status_handler.html_repr (self)
                + '<ul>'
                + '  <li><b>Total Hits:</b> %s'         % self.hit_counter
                + '  <li><b>Files Delivered:</b> %s'    % self.file_counter
                + '  <li><b>Cache Hits:</b> %s'         % self.cache_counter
                + '</ul>'
                )

    def get_propnames(self,uri):
        """ return the property names allowed for the given URI 

        In this method we simply return the above defined properties
        assuming that they are valid for any resource. 
        You can override this in order to return a different set
        of property names for each resource.
        
        """
        return self.PROPS


    def get_prop(self,uri,ns,propname):
        """ return the value of a given property

        uri        -- uri of the object to get the property of
        ns        -- namespace of the property
        pname        -- name of the property
        """
        if self.M_NS.has_key(ns):
            prefix=self.M_NS[ns]
        else:
            #print "Couldn't find property %s" % propname
            raise errors.DAV_NotFound
        mname=prefix+"_"+propname.replace("-", "_")
        try:
            m=getattr(self,mname)
            path = uri[len(self.urlroot):]
            r=m(path)
            return r
        except AttributeError:
            #logger.exception("Couldn't find method %s", mname)
            raise errors.DAV_NotFound


    def get_children(self, uri):
        """ return the child objects as URIs for the given URI """
        path = uri[len(self.urlroot):]
        files = self.filesystem.listdir(path)
        if type(files) != types.ListType:
            files = files.list
        filelist=[]
        for file in files:
            newloc = os.path.join(path,file)
            filelist.append(
                os.path.join(
                    self.urlroot,
                    newloc[1:])
                )

        return filelist


    """

    COPY/MOVE HANDLER

    These handler are called when a COPY or MOVE method is invoked by
    a client. In the default implementation it works as follows:

    - the davserver receives a COPY/MOVE method
    - the davcopy or davmove module will be loaded and the corresponding
      class will be initialized
    - this class parses the query and decides which method of the interface class
      to call:

      copyone for a single resource to copy
      copytree for a tree to copy (collection)
      (the same goes for move of course).

    - the interface class has now two options:
        1. to handle the action directly (e.g. cp or mv on filesystems)
        2. to let it handle via the copy/move methods in davcmd.

    ad 1) The first approach can be used when we know that no error can 
          happen inside a tree or when the action can exactly tell which
          element made which error. We have to collect these and return
          it in a dict of the form {uri: error_code, ...}

    ad 2) The copytree/movetree/... methods of davcmd.py will do the recursion
          themselves and call for each resource the copy/move method of the
          interface class. Thus method will then only act on a single resource.
          (Thus a copycol on a normal unix filesystem actually only needs to do
          an mkdir as the content will be copied by the davcmd.py function.
          The davcmd.py method will also automatically collect all errors and
          return the dictionary described above.
          When you use 2) you also have to implement the copy() and copycol()
          methods in your interface class. See the example for details.

    To decide which approach is the best you have to decide if your application
    is able to generate errors inside a tree. E.g. a function which completely
    fails on a tree if one of the tree's childs fail is not what we need. Then
    2) would be your way of doing it.
    Actually usually 2) is the better solution and should only be replaced by
    1) if you really need it.

    The remaining question is if we should do the same for the DELETE method.

    """

    ### MOVE handlers

    def moveone(self,src,dst,overwrite):
        """ move one resource with Depth=0 """
        return moveone(self,src,dst,overwrite)

    def movetree(self,src,dst,overwrite):
        """ move a collection with Depth=infinity """
        return movetree(self,src,dst,overwrite)

    ### COPY handlers

    def copyone(self,src,dst,overwrite):
        """ copy one resource with Depth=0 """
        return copyone(self,src,dst,overwrite)

    def copytree(self,src,dst,overwrite):
        """ copy a collection with Depth=infinity """
        return copytree(self,src,dst,overwrite)


    ### low level copy methods (you only need these for method 2)
    def copy(self,src,dst):
        """ copy a resource with depth==0 

        You don't need to bother about overwrite or not.
        This has been done already.

        return a success code or raise an exception if something fails
        """
        return 201


    def copycol(self,src,dst):
        """ copy a resource with depth==infinity 

        You don't need to bother about overwrite or not.
        This has been done already.

        return a success code or raise an exception if something fails
        """
        return 201

    

    ### some utility functions you need to implement

    def exists(self, path):
        """ return 1 or None depending on if a resource exists """
        try:
            self.filesystem.stat(path)
            return 1
        except:
            return None

    def is_collection(self, path):
        """ return 1 or None depending on if a resource is a collection """
        return self.filesystem.isdir(path)


    # Properties
    def _get_dav_getlastmodified(self, path):
        mtime = self.filesystem.stat(path)[stat.ST_MTIME]
        return time.strftime("%a, %d %b %Y %H:%M:%S %Z",time.localtime(mtime))

    def _get_dav_creationdate(self, path):
        mtime = self.filesystem.stat(path)[stat.ST_CTIME]
        return time.strftime("%a, %d %b %Y %H:%M:%S %Z",time.localtime(mtime))


    def _get_dav_resourcetype(self, path):
        """ return type of object """
        if self.filesystem.isfile(path):
            return constants.OBJECT
        else:
            return constants.COLLECTION
		
    def _get_dav_displayname(self, path):
        raise errors.DAV_Secret	# do not show

    def _get_dav_getcontentlength(self, path):
        """ return the content length of an object """
        if self.filesystem.isfile(path):
            return str(self.filesystem.stat(path)[stat.ST_SIZE])
        else:
            return "0"


# HTTP/1.0 doesn't say anything about the "; length=nnnn" addition
# to this header.  I suppose its purpose is to avoid the overhead
# of parsing dates...
IF_MODIFIED_SINCE = re.compile (
        'If-Modified-Since: ([^;]+)((; length=([0-9]+)$)|$)',
        re.IGNORECASE
        )

USER_AGENT = re.compile ('User-Agent: (.*)', re.IGNORECASE)

CONTENT_TYPE = re.compile (
        r'Content-Type: ([^;]+)((; boundary=([A-Za-z0-9\'\(\)+_,./:=?-]+)$)|$)',
        re.IGNORECASE
        )

get_header = medusa.http_server.get_header
get_header_match = medusa.http_server.get_header_match

def get_extension (path):
    dirsep = path.rfind('/')
    dotsep = path.rfind('.')
    if dotsep > dirsep:
        return path[dotsep+1:]
    else:
        return ''
