"""Extends the standard WebDAV handler with audiostore specific behaviour.

The only real difference is when a user tries to GET a directory, which
results in a specific function being called, which knows about the audiostore
MySQL database."""

import stat
import logging
import posixpath

import medusa.http_date

import webdav.webdav_handler


logger = logging.getLogger("audiostore.webdav")


class webdav_handler(webdav.webdav_handler.webdav_handler):

    def get_directory(self, request):
        path, params, query, fragment = request.split_uri()

        path = path[len(self.urlroot):]

        path = posixpath.join(path, "list", "index.html")
        
        # Translate it to a SQL hierarchy thinger
        hier = self.filesystem.build_sql_hier(path)

        print hier
        hier.urlroot = self.urlroot

        server = "http://" + request.channel.server.server_name
        if request.channel.server.port != 80:
            server += ":%d" % request.channel.server.port

        hier.server_name = server

        logger.info("generating a HTML index page")

        # FIXME: Give the 'hier' whatever query strings we got
        # with the request. This is used to sort the song list
        # in various ways

        if query:
            import cgi
            vars = cgi.parse_qs(query[1:])

            if vars.has_key('order'):
                # Find out what order parameters we had before, which
                # doesn't have a DESC modifier on them. For those, we
                # reverse the search order (i.e. apply the DESC modifier).
                old_order = [ x.strip() for x in hier.order.split(",") \
                              if x.find("DESC") == -1 ]

                new_order = [ key in old_order and key+" DESC" or key \
                              for key in vars['order'] ]

                hier.order = reduce(lambda c, a: c + ',' + a, new_order)

        hier.file = None

        fstat = hier.stat()
        file_length = fstat[stat.ST_SIZE]
        mtime = fstat[stat.ST_MTIME]

        try:
            file = hier.open('rb')
        except IOError:
            request.error (404)
            return

        request['Last-Modified'] = medusa.http_date.build_http_date (mtime)
        request['Content-Length'] = file_length
        self.set_content_type (path, request)

        # This method is also called by HEAD requests!
        if request.command == 'GET':
            request.push (self.default_file_producer (file))

        self.file_counter.increment()
        request.done()

    def _get_dav_getcontenttype(self, path):
        
        # Translate it to a SQL hierarchy thinger
        hier = self.filesystem.build_sql_hier(path)

        return hier.content_type()
