#!/usr/bin/env python

"""REMUS is a project to make a complete audio player platform, suitable
for smaller computer, not necessarily with a normal screen.

The REMUS player is the audio player part of this project, which produces
the actual sound from the various audio formats supported.
"""

import sys
import distutils
from distutils.core import setup
from distutils.extension import Extension
from commands import getstatusoutput, getoutput

VERSION_MAJOR = 0
VERSION_MINOR = 1
remusplayer_version = "%s.%s" % (VERSION_MAJOR, VERSION_MINOR)

def pkg_config(package):
    s, o = getstatusoutput("pkg-config --cflags-only-I %s" % package)
    if s != 0:
        print >> sys.stderr, "%s not found, I need this to continue" % package
        raise SystemExit

    includes = [ incdir[2:] for incdir in o.split() ]

    o = getoutput("pkg-config --cflags-only-other %s" % package)
    defines = [ tuple(define[2:].split("=")) for define in o.split() ]
    defines = [ len(d) == 2 and d or d + (None,) for d in defines ]

    o = getoutput("pkg-config --libs-only-l %s" % package)
    libs = [ lib[2:] for lib in o.split() ]

    o = getoutput("pkg-config --libs-only-L %s" % package)
    libdirs = [ libdir[2:] for libdir in o.split() ]

    o = getoutput("pkg-config --libs-only-other %s" % package)
    extra_link_args = o.split()

    return {
        'include_dirs'   : includes,
        'define_macros'  : defines,
        'library_dirs'   : libdirs,
        'libraries'      : libs,
        'extra_link_args': extra_link_args,
        }


pkg_gstreamer_play = pkg_config("gstreamer-play-0.6")
pkg_gstreamer_gconf = pkg_config("gstreamer-gconf-0.6")
pkg_gconf = pkg_config("gconf-2.0")

defines = pkg_gstreamer_play['define_macros']
defines += pkg_gstreamer_gconf['define_macros']
defines += pkg_gconf['define_macros']
defines += [('VERSION_MAJOR', VERSION_MAJOR),
            ('VERSION_MINOR', VERSION_MINOR),
            ('VERSION', '"%s"' % remusplayer_version)]

include_dirs = pkg_gstreamer_play['include_dirs']
include_dirs += pkg_gstreamer_gconf['include_dirs']
include_dirs += pkg_gconf['include_dirs']
 
library_dirs = pkg_gstreamer_play['library_dirs']
library_dirs += pkg_gstreamer_gconf['library_dirs']
library_dirs += pkg_gconf['library_dirs']

libraries = pkg_gstreamer_play['libraries']
libraries += pkg_gstreamer_gconf['libraries']
libraries += pkg_gconf['libraries']

extra_link_args = pkg_gstreamer_play['extra_link_args']
extra_link_args += pkg_gstreamer_gconf['extra_link_args']
extra_link_args += pkg_gconf['extra_link_args']

_remusplayermodule = Extension(
    name='_remusplayer',
    sources=['src/_remusplayermodule.c'],
    define_macros=defines,
    include_dirs=include_dirs,
    library_dirs=library_dirs,
    libraries=libraries,
    extra_compile_args=["-g"],
    extra_link_args=extra_link_args + ["-g"])

dist = setup(
    name="remusplayer",
    version="0.1",
    description="Audio player framework, wrapping various audio format players",
    author="Daniel Larsson",
    author_email="Daniel.Larsson@servicefactory.se",
    url="http://www.remus.org/player",
    long_description=__doc__,

    packages = ['remus', 'remus.player'],
    scripts = ['curses_player'],
    ext_package = "remus.player",
    ext_modules = [_remusplayermodule],
    classifiers = [
        "Development Status :: 0 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Multimedia :: Audio",
    ],
    verbose=1
    )
