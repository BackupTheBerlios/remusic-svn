"Install handler in the webserver for the audiostore"

import remus.database
import remus.audiostore
import remus.audiostore.mysql_filesys
import remus.audiostore.webdav_handler

def install(hs, cp):

    docroot = cp.get('server', 'defaultroot')
    as_prefix = cp.get('server', 'audiostore-prefix')

    # XXX Change user to something more reasonable!
    conn = remus.database.connect(host="localhost", user="root", db="remus")
    
    as_if = remus.audiostore.Interface(conn)
    
    # Create the MySQL filesystem, and give it to the WebDAV handler
    mys = remus.audiostore.mysql_filesys.mysql_filesystem(as_if.root())
    
    remus.audiostore.audiostore_file_root(docroot)
    
    wh = remus.audiostore.webdav_handler.webdav_handler(mys, as_prefix)
    hs.install_handler(wh)
