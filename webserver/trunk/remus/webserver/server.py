"""The HTTP server, serving requests to the various components of Remus.
"""

# standard modules
import os
import logging
import logging.config
import ConfigParser

# twisted modules
from twisted.internet import app
from twisted.web import static, server, script

# remus modules
import remus.audiostore


configfile = ("/usr/local/etc/remus/remus.conf",
              "%s/.remus.conf" % os.environ["HOME"])

cp = ConfigParser.ConfigParser({
    'passwd':            'remus',
    'serverport':        '80',
    'monitorport':       '9999',
    'defaultroot':       '/usr/local/libdata/remus',
    'audiostore-prefix': '/music',
    })

cp.read(configfile)

serverport = int(cp.get('server', 'serverport'))
docroot = cp.get('server', 'defaultroot')

logging.config.fileConfig(configfile, {
    'class':  "StreamHandler",
    'format': '[%(asctime)s] %(name)s: %(message)s'})

logger = logging.getLogger("remus.webserver")

logger.info("Starting remus server")

# The audiostore must know the docroot to find the XSL stylesheets
remus.audiostore.audiostore_file_root(docroot)

root = static.File(docroot)
root.ignoreExt(".rpy")
root.processors = {'.rpy': script.ResourceScript}

application = app.Application('remus')
application.listenTCP(serverport, server.Site(root))
application.run()
