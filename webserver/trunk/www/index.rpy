import os
import remus.webserver.remuspage

resource = remus.webserver.remuspage.RemusPage(
    templateDirectory=os.path.dirname(__file__))
