#!/usr/local/bin/python

"""REMUS is a project to make a complete audio player platform, suitable
for smaller computer, not necessarily with a normal screen.

The REMUS webserver is the primary net interface to the box used for
downloading/uploading and managing the box.
"""

import distutils
from distutils.core import setup, Command
from distutils.command import install
from distutils import log


import os
config_files_path = os.path.join("etc", "remus")

class gettext_install(Command):
    description = "Install gettext catalog files"

    user_options = []
    
    def initialize_options(self):
        self.install_dir = None
        self.outfiles = []

    def finalize_options (self):
        self.set_undefined_options(
            'install',
            ('install_data', 'install_dir'),
            )

    def run(self):
        import os
        dir = os.path.join(self.install_dir, 'share/locale')
        for file in os.listdir('po'):
            if file[-3:] == '.po':
                lang = os.path.splitext(file)[0]
                os.system("msgfmt -o po/%s.mo po/%s.po" % (lang, lang))
                outfile = self.distribution.metadata.name + '.mo'
                (out, _) = self.copy_file(
                    os.path.join("po", lang+'.mo'),
                    os.path.join(dir, lang, "LC_MESSAGES", outfile))
                self.outfiles.append(out)

    def get_outputs (self):
        return self.outfiles


class webserver_setup (Command):

    # Brief (40-50 characters) description of the command
    description = "Executes extra code after file installation is done"

    # List of option tuples: long name, short name (None if no short
    # name), and help string.
    user_options = []


    def initialize_options (self):
        self.install_dir = None

    def finalize_options (self):
        self.set_undefined_options('install',
                                   ('install_data', 'install_dir'),
                                   )

    # finalize_options()


    def run (self):
        base = os.path.join(self.install_dir, config_files_path)
        try:
            conffile = os.path.join(base, "remus.conf")
            deffile = os.path.join(base, "remus.conf.default")
            if not os.path.exists(conffile):
                log.info("installing remus.conf")
                conf = open(conffile, "w")
                conf.write(open(deffile).read())
                conf.close()
            else:
                log.info("preserving your old remus.conf in %s", base)

        except:
            import traceback
            traceback.print_exc()
            print "Failed to install configuration file!"

    # run()

# class x


install.install.sub_commands.append(('webserver_setup', None))
install.install.sub_commands.append(('gettext_install', None))


dist = setup(
    name="remus-server",
    version="0.3.0",
    description="Webserver used in the REMUS project ",
    author="Daniel Larsson",
    author_email="Daniel.Larsson@servicefactory.se",
    url="http://www.remus.org/webserver",
    long_description=__doc__,

    packages = ['remus', 'remus.i18n',
                'remus.webserver',
                'remus.webserver.handlers',
                'remus.webserver.webdav'],
    scripts = ['remus_server'],
    data_files = [('libdata/remus',
                   ('www/index.rpy',
                    'www/lang.rpy',
                    'www/RemusPage.html')),
                  ('libdata/remus/styles',
                   ('styles/remus.css',
                    'styles/toppages.css',
                    'styles/menu.css',)),
                  ('libdata/remus/images',
                   ('www/images/da.png',
                    'www/images/en.png',
                    'www/images/sv.png')),
                  ('libdata/remus/scripts',
                   ('www/scripts/menu.js',)),
                  (config_files_path,
                   ('remus.conf.default',)),
                  ],
    classifiers = [
        "Development Status :: 0 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Multimedia :: Audio",
    ],
    cmdclass={'webserver_setup': webserver_setup,
              'gettext_install': gettext_install},
    verbose=1
    )

