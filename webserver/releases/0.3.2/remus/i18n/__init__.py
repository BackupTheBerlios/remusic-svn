#
# Copyright (C) 2004 Daniel Larsson
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
#

"""Internationalization interface.

This module provides functions to control what language text is
presented as.
"""

__author__ = 'Daniel Larsson, <daniel.larsson@servicefactory.se>'

from Init import *

# Load modules in this package, they will add the translation domains
def init():
    import os
    files = reduce(lambda c, dir: c+os.listdir(dir), __path__, [])
    modules = filter(lambda file: file[-2:] == "py" and
                     'a' <= file[0] <= 'z', files)
    
    for module in modules:
	py_module = module[:-3]
	try:
	    exec "import %s" % py_module in globals()
	except ImportError:
	    import sys
	    logger.warning('Failed to import %s (%s: %s)\n' %
			    (py_module, sys.exc_type, sys.exc_value))
	except NameError:
	    import sys
	    logger.warning('Failed to import %s (%s: %s)\n' %
			    (py_module, sys.exc_type, sys.exc_value))

	except:
	    import sys
	    raise sys.exc_type, sys.exc_value, sys.exc_traceback

init()
