# -*- mode: python -*-
#
# Copyright (C) 2004 Daniel Larsson
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
#

import remus.webserver.remuspage

_ = lambda a: a

class Index(remus.webserver.remuspage.RemusPage):

    title = _("Remus music server")


    def getSubtemplate(self, request):
        _ = request.getSession(remus.i18n.ITranslator).gettext('remus-server')
        
        return '<div class="text">' + \
               _("Browse the music database to view its contents, " \
                 "and to download songs. You can upload songs to " \
                 "the database through the web as well.") + \
                 "</div>"

resource = Index()
