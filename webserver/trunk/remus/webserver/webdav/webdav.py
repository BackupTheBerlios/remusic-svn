# -*- Mode: Python -*-
#
#       Author: Daniel Larsson <Daniel.Larsson@servicefactory.se>
#       Copyright 2003 by Daniel Larsson
#                                                All Rights Reserved.
#

# standard python modules
import mimetypes
import os
import posixpath
import re
import stat
import string
import sys
import time
import types
import urllib
import urlparse
import logging

try:
    from cStringIO import StringIO
except ImportErrot:
    from StringIO import StringIO

# twisted modules
import twisted.protocols.http
import twisted.web.error
import twisted.web.microdom
import twisted.web.resource
import twisted.web.server
import twisted.web.static

# local modules
import errors
import utils

unquote = urllib.unquote

logger = logging.getLogger("remus.webserver.webdav")


# definition for resourcetype
COLLECTION = 1
OBJECT = None
DAV_PROPS = [
    'creationdate',
    'displayname',
    'getcontentlanguage',
    'getcontentlength',
    'getcontenttype',
    'getetag',
    'getlastmodified',
    'lockdiscovery',
    'resourcetype',
    'source',
    'supportedlock',
    ]


# Request classes in propfind

RT_ALLPROP=1
RT_PROPNAME=2
RT_PROP=3


class MOVE:
    def __init__(self, resource, request, src, dst, overwrite):
        self.__resource = resource
        self.__request = request
	self.__src = src
	self.__dst = dst
	self.__overwrite = overwrite

    def single_action(self):
        """ move a normal resource.

	We try to move it and return the result code.
	This is for Depth==0
	"""

        # Create a fake request to locate the destination
        class _empty:
            pass
        fake_channel = _empty()
        fake_channel.transport = None
        dst_req = twisted.web.server.Request(fake_channel, None)
        dst_req.path = self.__dst
        dst_req.prepath = []
        dst_req.postpath = string.split(dst_req.path[1:], '/')

        # Find resource
        dst_rsc = self.__request.site.getResourceFor(dst_req)

	# test if dest exists and overwrite is false
	if not isinstance(dst_rsc, twisted.web.error.NoResource) and \
               not self.__overwrite:
            raise errors.DAV_Error, twisted.protocols.http.PRECONDITION_FAILED
        
	# test if src and dst are the same
	if self.__src == self.__dst:
            raise errors.DAV_Error, twisted.protocols.http.FORBIDDEN

	return self.__resource.moveone(self.__dst,self.__overwrite)


    def tree_action(self):
        """ move a tree of resources (a collection)

	Here we return a multistatus xml element.

	"""

        # Create a fake request to locate the destination
        class _empty:
            pass
        fake_channel = _empty()
        fake_channel.transport = None
        dst_req = twisted.web.server.Request(fake_channel, None)
        dst_req.path = self.__dst
        dst_req.prepath = []
        dst_req.postpath = string.split(dst_req.path[1:], '/')

        # Find resource
        dst_rsc = self.__request.site.getResourceFor(dst_req)

	# test if dest exists and overwrite is false
	if not isinstance(dst_rsc, twisted.web.error.NoResource) and \
               not self.__overwrite:
            logger.info("File found and no overwrite flag set")
            raise errors.DAV_Error, twisted.protocols.http.PRECONDITION_FAILED
        
	# test if src and dst are the same
	if self.__src == self.__dst:
            raise errors.DAV_Error, twisted.protocols.http.FORBIDDEN

	result = self.__resource.movetree(
            self.__src,
            self.__dst,
            self.__overwrite)

	if not result:
            return None

	# create the multistatus XML element
	return make_xmlresponse(result)


class WebDAV(twisted.web.resource.Resource):

    valid_commands = ['GET', 'HEAD', 'PUT', 'OPTIONS',
                      'PROPFIND', 'PROPPATCH', 'MKCOL',
                      'MOVE']

    # Properties

    PROPS = {
        "DAV:" : DAV_PROPS,
        }


    # here we define which methods handle which namespace
    # the first item is the namespace URI and the second one
    # the method prefix
    # e.g. for DAV:getcontenttype we call _get_davcontenttype()
    M_NS = {"DAV:" : "_get_dav"}


    # Pathnames that are tried when a URI resolves to a directory name
    directory_defaults = [
            'index.html',
            'default.html'
            ]

    def render(self, request):
        logger.info("Incomming %s request for %s", request.method, request.path)
        if request.method not in self.valid_commands:
            raise twisted.web.server.UnsupportedMethod(self.valid_commands)

        mname = 'render' + request.method
        if not hasattr(self, mname):
            request.setResponseCode(twisted.protocols.http.NOT_IMPLEMENTED)
            return
        method = getattr(self, mname)
        return method(request)


    def renderOPTIONS(self, request):
        request.setHeader("Allow", ", ".join(self.valid_commands))
        request.setHeader("Content-Type", "text/plain")
        request.setHeader("DAV", "1")
        return ""


    def renderPROPFIND(self, request):
        len = int(request.getHeader("Content-Length"))
        self.request = request

        depth = request.getHeader('Depth')
        if not depth:
            depth = 'infinity'

        try:
            self.stat()
        except IOError:
            # logger.exception("Failed to stat %s", path)
            request.setResponseCode(twisted.protocols.http.NOT_FOUND)
            return

        #print "PROPFIND request: depth = %s" % depth
        propf = PropFind(self, depth)

        if request.content:
            propf.read_propfind(request.content.read())

        try:
            data = propf.createResponse() + '\n'
            #print "PROPFIND response: %s" % data
        except errors.DAV_Error, (errorcode, dd):
            request.setResponseCode(errorcode)
            return

        request.setResponseCode(twisted.protocols.http.MULTI_STATUS)
        return data


    def renderGET(self, request):

        if self.isdir():

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

            # Did we finish the request?
            if request.finished:
                return ''

        elif not self.isfile ():
            request.setResponseCode(twisted.protocols.http.NOT_FOUND)
            return ''

        try:
            file = self.open('rb')
        except IOError:
            request.setResponseCode(twisted.protocols.http.NOT_FOUND)
            return ''

        file_stat = self.stat()
        mtime = file_stat[stat.ST_MTIME]
        file_length = file_stat[stat.ST_SIZE]

        cached = request.setLastModified(mtime)
        request.setHeader('Content-Length', file_length)
        self.set_content_type (request)

        if not cached and request.method == 'GET':
            # return data
            twisted.web.static.FileTransfer(file, file_length, request)
            # and make sure the connection doesn't get closed
            return twisted.web.server.NOT_DONE_YET

        return ''

    renderHEAD = renderGET


    def renderMKCOL(self, request):
        path, params, query, fragment = request.split_uri()

        if '%' in path:
            path = unquote (path)

        path = path[len(self.urlroot):]

        # test if file already exists
        try:
            self.stat(path)
            request.setResponseCode(twisted.protocols.http.NOT_ALLOWED)
            return
        except:
            pass

        # test if parent exists
        h, t = os.path.split(path[:-1])
        try:
            self.stat(h)
        except:
            request.setResponseCode(twisted.protocols.http.CONFLICT)
            return

        try:
            self.mkdir(path)
        except:
            request.setResponseCode(twisted.protocols.http.FORBIDDEN)


    def renderDELETE(self, request):
        request.setResponseCode(twisted.protocols.http.FORBIDDEN)


    def renderPUT(self, request):
        try:
            l = int(request.get_header("Content-Length"))
            logger.info("Incomming file: %d bytes long", l)

            path, params, query, fragment = request.split_uri()


            if '%' in path:
                path = unquote (path)

                path = path[len(self.urlroot):]

            if request.has_key("Content-Type"):
                content_type = request.getHeader("Content-Type")

            try:
                file = self.open(path, 'w+')
                request.collector = put_collector(file, l, request, 0)

                # no terminator while receiving PUT data
                request.channel.set_terminator (None)
            except:
                request.setResponseCode(424)
        except:
            request.setResponseCode(twisted.protocols.http.LENGTH_REQUIRED)


    def renderMOVE(self, request):
        "Move resource"

	try:
	    self.copymove(request, MOVE)
	except errors.DAV_Error, (ec,dd):
	    request.setResponseCode(ec)
        

    def copymove(self, request, CLASS):
	""" common method for copying or moving objects """

	# get the source URI
	source_uri = urllib.unquote(request.path)

	# get the destination URI
	dest_uri = request.getHeader("Destination")
	dest_uri = urllib.unquote(dest_uri)

        import urlparse
        scheme, netloc, path, query, frag = urlparse.urlsplit(dest_uri)

        # Assume we're moving within this host. Ignore query and frag
        # parts.
        dest_uri = path

	# Overwrite?
	overwrite = 1
	result_code = twisted.protocols.http.NO_CONTENT
	if request.getAllHeaders().get("Overwrite", 'T'):
            overwrite = None
            result_code = twisted.protocols.http.CREATED

	# instanciate ACTION class
    	cp = CLASS(self, request, source_uri, dest_uri, overwrite)

	# Depth?
	d = "infinity"
	if request.getAllHeaders().has_key("Depth"):
	    d = request.getHeader('Depth')
	    if d != "0" and d != "infinity": 
    		request.setResponseCode(twisted.protocols.http.BAD_REQUEST)
		return
	    if d == "0":	
		res = cp.single_action()
                request.setResponseCode(res)
		return

	# now it only can be "infinity" but we nevertheless check
        # for a collection
        if self.isdir():
	    try:
		res = cp.tree_action()
	    except errors.DAV_Error, (ec, dd):
                print "ERROR!!!"
		request.setResponseCode(ec, dd)
		return
	else:
	    try:
		res = cp.single_action()
	    except errors.DAV_Error, (ec, dd):
		request.setResponseCode(ec)
		return

        print "MOVE/COPY response: %s" % res
	if res:
            request.setHeader('content-type', 'text/xml; charset="utf-8"')
            request.setResponseCode(twisted.protocols.http.MULTI_STATUS)
            request.write(res)
	else:
            request.setResponseCode(result_code)


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
            if self.isfile (p):
                path = p
                found = 1
                break
        if not found:
            request.setResponseCode(twisted.protocols.http.NOT_FOUND)

        return path
        


    def set_content_type (self, request):
        try:
            request.setHeader('Content-Type', self.content_type())
            return
        except AttributeError:
            pass
        
        typ, encoding = mimetypes.guess_type(request.path)
        if typ is not None:
            request.setHeader('Content-Type', typ)
        else:
            # TODO: test a chunk off the front of the file for 8-bit
            # characters, and use application/octet-stream instead.
            request.setHeader('Content-Type', 'text/plain')


    def getPropNames(self):
        """ return the property names allowed for the given URI 

        In this method we simply return the above defined properties
        assuming that they are valid for any resource. 
        You can override this in order to return a different set
        of property names for each resource.
        
        """
        return self.PROPS


    def getProp(self, ns, propname):
        """ return the value of a given property

        ns           -- namespace of the property
        pname        -- name of the property
        """
        if self.M_NS.has_key(ns):
            prefix=self.M_NS[ns]
        else:
            #print "Couldn't find property %s" % propname
            raise errors.DAV_NotFound
        mname=prefix+"_"+propname.replace("-", "_")
        try:
            m = getattr(self,mname)
            r = m()
            print "%s (%s):%s is %s" % (self.collection.cwd(),
                                        self.collection, mname, r)
            return r
        except AttributeError:
            #logger.exception("Couldn't find method %s", mname)
            raise errors.DAV_NotFound


    """

    COPY/MOVE HANDLER

    These handlers are called when a COPY or MOVE method is invoked by
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

    def moveone(self, src, dst, overwrite):
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


    # Properties
    def _get_dav_getlastmodified(self):
        mtime = self.stat()[stat.ST_MTIME]
        return time.strftime("%a, %d %b %Y %H:%M:%S %Z",time.localtime(mtime))

    def _get_dav_creationdate(self):
        mtime = self.stat()[stat.ST_CTIME]
        return time.strftime("%a, %d %b %Y %H:%M:%S %Z",time.localtime(mtime))


    def _get_dav_resourcetype(self):
        """ return type of object """
        if self.isfile():
            return OBJECT
        else:
            return COLLECTION
		
    def _get_dav_displayname(self):
        raise errors.DAV_Secret	# do not show

    def _get_dav_getcontentlength(self):
        """ return the content length of an object """
        if self.isfile():
            return str(self.stat()[stat.ST_SIZE])
        else:
            return "0"

    def _get_dav_getcontenttype(self):
        return self.content_type()



class PropFind:
    """ parse a propfind xml element and extract props 

    It will set the following instance vars:

    request_class	: ALLPROP | PROPNAME | PROP
    proplist	: list of properties
    nsmap		: map of namespaces
    
    The list of properties will contain tuples of the form
    (element name, ns_prefix, ns_uri)
    
    """


    def __init__(self, resource, depth):
        self.request_type = None
	self.nsmap = {}
	self.proplist = {}
	self.default_ns = None
	self.__resource = resource
	self.__depth = str(depth)
        self.__baseuri = resource.request.path
        
    def read_propfind(self, xml_doc):
        self.request_type,
	self.proplist,
	self.namespaces = utils.parse_propfind(xml_doc)

    def createResponse(self):
        """ create the multistatus response 

	This will be delegated to the specific method
	depending on which request (allprop, propname, prop)
	was found.
	
	If we get a PROPNAME then we simply return the list with empty
	values which we get from the interface class
	
	If we get an ALLPROP we first get the list of properties and then
	we do the same as with a PROP method.
	
	"""
	
	if self.request_type == RT_ALLPROP:
	    return self.create_allprop()
        if self.request_type == RT_PROPNAME:
	    return self.create_propname()
        if self.request_type == RT_PROP:
	    return self.create_prop()
	# no body means ALLPROP!
	return self.create_allprop()

	
    def create_propname(self):
        """ create a multistatus response for the prop names """
	res = self.__resource

	# create the document generator
	ms = twisted.web.microdom.lmx("D:multistatus")
	ms["xmlns:D"] = "DAV:"
	
        pnames = res.getPropNames()
        re = self.mk_propname_response(res, self.__baseuri, pnames, ms)

        if self.__depth == "1":
            for name in res.listNames():
                resource = res.getChild(name, res.request)
                pnames = resource.getPropNames()
                re = self.mk_propname_response(resource,
                                               posixpath.join(self.__baseuri,
                                                              name),
                                               pnames,
                                               ms)

        # *** depth=="infinity"	 
		    
	return twisted.web.microdom.Document(ms.node).toxml()


    def create_allprop(self):
	""" return a list of all properties """
	self.proplist = {}
	self.namespaces = []
	for ns, plist in self.__resource.getPropNames().items():
	    self.proplist[ns] = plist
	    self.namespaces.append(ns)
	return self.create_prop()


    def create_prop(self):
        """ handle a <prop> request

	This will
	
	1. set up the <multistatus>-Framework
	
	2. read the property values for each URI 
	(which is dependant on the Depth header)
	This is done by the getPropvalues() method.
	
	3. For each URI call the append_result() method
	to append the actual <result>-Tag to the result
	document.
	
	We differ between "good" properties, which have been
	assigned a value by the interface class and "bad" 
	properties, which resulted in an error, either 404
	(Not Found) or 403 (Forbidden).
	
	"""

        resource = self.__resource
        
	# create the document generator
	ms = twisted.web.microdom.lmx("D:multistatus")
	ms["xmlns:D"] = "DAV:"
	
	good_props, bad_props = self.getPropvalues(resource)
	res = self.mk_prop_response(resource,
                                    self.__baseuri,
                                    good_props, bad_props, ms)
	    
	if self.__depth == "1":
            for name in resource.listNames():
                child = resource.getChild(name, resource.request)
                good_props, bad_props = self.getPropvalues(child)
 
                self.mk_prop_response(child,
                                      posixpath.join(self.__baseuri,
                                                     name),
                                      good_props,
                                      bad_props,
                                      ms)

	return twisted.web.microdom.Document(ms.node).toxml()


    def mk_propname_response(self, resource, uri, propnames, doc):
        """ make a new <prop> result element for a PROPNAME request 

	This will simply format the propnames list.
	propnames should have the format {NS1 : [prop1, prop2, ...], NS2: ...}
	
	"""
	re = doc.add("D:response")

	# write href information
	href = re.add("D:href")
	huri = href.text(urllib.quote(uri))
	
	ps = re.add("D:propstat")
	nsnum = 0
	
	for ns, plist in propnames.items():
            # write prop element
            pr = ps.add("D:prop")
            nsp = "ns" + str(nsnum)
            pr["xmlns:"+nsp] = ns
            nsnum = nsnum + 1

            # write propertynames
            for p in plist:
                pe = pr.add(nsp+":"+p)

	    

    def mk_prop_response(self, resource, uri, good_props, bad_props, doc):
        """ make a new <prop> result element 

	We differ between the good props and the bad ones for
	each generating an extra <propstat>-Node (for each error
	one, that means).
	
	"""
	re = doc.add("D:response")
        
	# append namespaces to response
	nsnum = 0
	for nsname in self.namespaces:
            re["xmlns:ns" + str(nsnum)] = nsname
            nsnum = nsnum + 1
	    
	# write href information
	href = re.add("D:href")
	huri = href.text(urllib.quote(uri))

	# write good properties
	if good_props:
            ps = re.add("D:propstat")
            gp = ps.add("D:prop")

            for ns in good_props.keys():
                ns_prefix = "ns" + str(self.namespaces.index(ns)) + ":"
                for p, v in good_props[ns].items():
                    pe = gp.add(ns_prefix + str(p))
                    if p == "resourcetype":
                        if v == "1":
                            ve = pe.add("D:collection")
                    else:
                        pe.text(str(v))

            s = ps.add("D:status")
            t = s.text("HTTP/1.1 200 OK")

	# now write the errors!
	if len(bad_props.items()):
            # write a propstat for each error code
            for ecode in bad_props.keys():
                ps = re.add("D:propstat")
                bp = ps.add("D:prop")

                for ns in bad_props[ecode].keys():
                    ns_prefix = "ns" + str(self.namespaces.index(ns)) + ":"
                    for p in bad_props[ecode][ns]:
                        pe = bp.add(ns_prefix+str(p))

                s = ps.add("D:status")
                t = s.text(gen_estring(ecode))


    def getPropvalues(self, resource):
        """ create lists of property values for an URI 

	We create two lists for an URI: the properties for
	which we found a value and the ones for which we
	only got an error, either because they haven't been
	found or the user is not allowed to read them.
	
	"""
	good_props = {}
	bad_props = {}
	
	for ns, plist in self.proplist.items():
	    good_props[ns] = {}
	    bad_props = {}
            
	    for prop in plist:
                try:
                    r = resource.getProp(ns, prop)
                    good_props[ns][prop] = str(r)
                except errors.DAV_Error, error_code:
                    ec = error_code[0]
                    # ignore props with error_code if 0 (invisible)
                    if ec == 0: continue
                    if bad_props.has_key(ec):
                        if bad_props[ec].has_key(ns):
                            bad_props[ec][ns].append(prop)
                        else:
                            bad_props[ec][ns] = [prop]
                    else:
                        bad_props[ec] = {ns:[prop]}

	return good_props, bad_props



USER_AGENT = re.compile ('User-Agent: (.*)', re.IGNORECASE)

CONTENT_TYPE = re.compile (
        r'Content-Type: ([^;]+)((; boundary=([A-Za-z0-9\'\(\)+_,./:=?-]+)$)|$)',
        re.IGNORECASE
        )


def get_extension (path):
    dirsep = path.rfind('/')
    dotsep = path.rfind('.')
    if dotsep > dirsep:
        return path[dotsep+1:]
    else:
        return ''

def gen_estring(ecode):
    """ generate an error string from the given code """
    ec = int(str(ecode))
    return "HTTP/1.1 %s %s" % (ec,
                               twisted.protocols.http.RESPONSES.get(ec, ''))
