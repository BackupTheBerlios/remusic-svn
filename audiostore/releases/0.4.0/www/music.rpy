# -*- mode:python -*-

import remus.audiostore
import remus.db_connect
import remus.webserver.audiostore
        
conn = remus.db_connect.set_current_user(user="root")

audiostore = remus.audiostore.Interface(conn)
resource = remus.webserver.audiostore.ASWrapper(audiostore.root())
