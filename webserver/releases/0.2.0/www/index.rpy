# -*- mode: python -*-

import logging
import remus.webserver.remuspage
import remus.i18n
_ = remus.i18n.dgettext('remus-server')

logger = logging.getLogger("remus.webserver")

class Index(remus.webserver.remuspage.RemusPage):

    title = _("Remus music server")

    template = '<div class="text">' + \
               _("Browse the music database to view its contents, " \
                 "and to download songs. You can upload songs to " \
                 "the database through the web as well.") + \
                 "</div>"

resource = Index()
