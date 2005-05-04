"Read remus configuration"


import os, sys
import ConfigParser
import logging.config

def init():
    etcpath = os.path.join(sys.prefix, "etc")

    if not os.path.isdir(etcpath):
        etcpath = "/etc"

    configfile = [os.path.join(etcpath, "remus", "remus.conf")]

    if os.environ.has_key("HOME"):
        configfile.append(os.path.join(os.environ["HOME"], ".rcremus"))

    cp = ConfigParser.ConfigParser({
        'passwd':            'remus',
        'serverport':        '80',
        'monitorport':       '9999',
        'defaultroot':       '/var/lib/remus',
        'audiostore-prefix': '/music',
        'uid':               '1000',
        'gid':               '100',
        'musicbrainz-server':''
        })
    
    cp.read(configfile)

    logging.config.fileConfig(configfile, {
        'class':  "StreamHandler",
        'format': '%(name)s: %(message)s'})

    return cp

config = init()
