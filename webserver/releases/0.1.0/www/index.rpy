# -*- mode: python -*-

import os
import gettext

import remus.webserver.remuspage

t = gettext.translation('remusserver', '/usr/local/share/locale', fallback=True)
_ = t.gettext

class Index(remus.webserver.remuspage.RemusPage):

    title = _("Remus music server")

    template = '<div class="text">' + \
_("""Browse the music database to view its contents, and to download songs.
You can upload songs to the database through the web as well.""") + \
    "</div>"

resource = Index()
