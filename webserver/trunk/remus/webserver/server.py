"""The HTTP server, serving requests to the various components of Remus.
"""

# standard modules
import os
import sys
import string
import logging
import logging.config
import asyncore
import ConfigParser

# medusa modules
import medusa.http_server
import medusa.monitor
import medusa.filesys
import medusa.default_handler
import medusa.status_handler
import medusa.auth_handler
import medusa.resolver
import medusa.logger

# remus modules
import remus.database
import mysql_authorizer
import handlers

# Executed in the main namespace to enable introspection through the monitor
# service.

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

monitorport = int(cp.get('server', 'monitorport'))
serverport = int(cp.get('server', 'serverport'))
docroot = cp.get('server', 'defaultroot')

logging.config.fileConfig(configfile, {
    'class':  "StreamHandler",
    'format': '[%(asctime)s] %(name)s: %(message)s'})


logger = logging.getLogger("remus.webserver")

rs = medusa.resolver.caching_resolver ('127.0.0.1')
lg = medusa.logger.file_logger (sys.stdout)

ms = medusa.monitor.secure_monitor_server (
    cp.get('server', 'passwd'),
    '127.0.0.1',
    monitorport)


hs = medusa.http_server.http_server('', serverport, rs, lg)

# Add a default, file system handler
fs = medusa.filesys.os_filesystem (docroot)
dh = medusa.default_handler.default_handler (fs)
hs.install_handler (dh)

#logger.info("Connecting to the Remus database")

#mysql_conn = database.connect(
#    host="localhost", user="root", db="mysql")

logger.info("Installing handlers")
handlers.import_handlers()
handlers.install_handlers(hs, cp)

# Add a status handler as well
sh = medusa.status_handler.status_extension([hs,ms,rs])
hs.install_handler (sh)

# Adding missing response code
medusa.http_server.http_request.responses[207] = "Multi-Status"
medusa.http_server.http_request.responses[424] = "Failed dependency"

# Away we go
if '-p' in sys.argv:
    def profile_loop ():
        try:
            asyncore.loop()
        except KeyboardInterrupt:
            pass
    import profile
    profile.run ('profile_loop()', 'profile.out')
else:
    asyncore.loop()
