#!/usr/bin/env python

"""REMUS is a project to make a complete audio player platform, suitable
for smaller computer, not necessarily with a normal screen.

The REMUS player is the audio player part of this project, which produces
the actual sound from the various audio formats supported.
"""

import distutils
from distutils.core import setup
from distutils.command import install
from distutils.core import Command
from distutils import log


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
