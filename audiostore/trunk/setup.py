#!/usr/bin/env python

"""audiostore is a WebDAV server on top of a MySQL database for storing
audio files in various formats (MP3, Ogg, SID, ...).

"""

import os
import distutils
from distutils.core import setup
from distutils.command import install
from distutils.command import build
from distutils.core import Command
from distutils import log


SQL_XML_FILES = (
    'db/audiostore.xml',
    )

class audiostore_build (Command):

    description = "Builds additional files"

    user_options = []

    def initialize_options (self):
        pass

    def finalize_options (self):
        pass
        
    def run (self):
        # Generate the sql files
        import os
        for file in SQL_XML_FILES:
            fname = os.path.splitext(os.path.basename(file))[0]
            cmd = "xsltproc -o remus/audiostore/db_%s.py db/makepython.xsl %s " % (fname, file)
            os.system(cmd)
            os.system("xsltproc -o db/%s.sql db/makesql.xsl %s" % (fname, file))


class audiostore_setup (Command):

    # Brief (40-50 characters) description of the command
    description = "Executes extra code after file installation is done"

    # List of option tuples: long name, short name (None if no short
    # name), and help string.
    user_options = []


    def initialize_options (self):
        self.install_dir = None

    # initialize_options()


    def finalize_options (self):
        self.set_undefined_options('install',
                                   ('install_data', 'install_dir'),
                                   )

    # finalize_options()


    def run (self):
        # Populate mysql
        log.info("creating MySQL tables (unless they already exist)")
        base = os.path.join(self.install_dir, "etc/remus/audiostore")
        os.system("mysql < %s" % os.path.join(base, "audiostore.sql"))

    # run()

# class audiostore_setup


install.install.sub_commands.append(('audiostore_setup', None))
build.build.sub_commands.insert(0, ('audiostore_build', None))

dist = setup(
    name="audiostore",
    version="0.1",
    description="WebDAV server for storing audio files",
    author="Daniel Larsson",
    author_email="Daniel.Larsson@servicefactory.se",
    url="http://www.remus.org/audiostore",
    long_description=__doc__,

    packages = ['remus', 'remus.audiostore', 'remus.webserver.handlers'],
    scripts = ['audiostore_resync'],
    data_files = [('etc/remus/audiostore',
                   ('db/audiostore.sql',)),
                  ('libdata/remus/styles',
                   ('styles/audiostore.css',
                    'styles/index.html.xsl',
                    'styles/m3u.xsl',
                    'styles/param.xsl')),
                  ],
    classifiers = [
        "Development Status :: 0 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Multimedia :: Audio",
    ],
    verbose=1,
    cmdclass={'audiostore_setup': audiostore_setup,
              'audiostore_build': audiostore_build}
    )
