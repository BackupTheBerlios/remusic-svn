#
# Import all handlers in this package, to let them register themselves
#

import os
import logging

_logger = logging.getLogger("remus.webserver")

_handlers = []

def import_handlers():

    for d in __path__:
        files = [ file for file in os.listdir(d)
                  if os.path.splitext(file)[1] == ".py"
                  and file != "__init__.py" ]


        for module in files:
            module = os.path.splitext(module)[0]
            modname = "remus.webserver.handlers." + module
            root = __import__(modname)
            _handlers.append(root.webserver.handlers.__dict__[module])

def install_handlers(httpserver, config):
    """Let handlers in this package install themselves in the http server"""

    for handler in _handlers:
        try:
            handler.install(httpserver, config)
            _logger.info("Installed %s handler", handler.__name__)
        except AttributeError:
            _logger.exception("Failed to install %s, not a handler??",
                             handler.__name__)
