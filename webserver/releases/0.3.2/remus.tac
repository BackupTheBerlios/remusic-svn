"""The HTTP server, serving requests to the various components of Remus.
"""

# standard modules
import os
import sys
import logging
import logging.config
import ConfigParser

# twisted modules
from twisted.application import internet, service
from twisted.web import static, server, script

from remus.webserver import config

serverport = config.getint('server', 'serverport')
uid = config.getint('server', 'uid')
gid = config.getint('server', 'gid')
docroot = config.get('server', 'defaultroot')

logger = logging.getLogger("remus.webserver")


# Set up translation module
import remus.i18n

# Start out with english
#remus.i18n.install('en')
#_ = remus.i18n.dgettext('remus-server')


logger.info("Starting remus server")

# The audiostore must know the docroot to find the XSL stylesheets
try:
    import remus.audiostore
    remus.audiostore.audiostore_file_root(docroot)
except ImportError:
    pass

root = static.File(docroot)
root.ignoreExt(".rpy")
root.processors = {'.rpy': script.ResourceScript}

application = service.Application('remus', uid=uid, gid=gid)

internet.TCPServer(serverport, server.Site(root)
                   ).setServiceParent(
    service.IServiceCollection(application))
