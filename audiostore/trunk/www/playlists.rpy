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

import sqlquery

import remus.db_connect
import remus.webserver.remuspage
from remus.audiostore.db_audiostore import *
import remus.i18n

_ = lambda a: a


class Playlist(remus.webserver.remuspage.RemusPage):

    def getSubtemplate(self, request):
        _ = request.getSession(remus.i18n.ITranslator).gettext('remus-audiostore')
        self.title = _("Playlist administration")
        self.emptyList = _("No playlists defined")
        
        return '<div class="text">' + \
               _("Defined playlists:") + \
               '''<ul model="playlists" view="List">
               <li pattern="emptyList">%s</li>
               <li pattern="listItem" view="Text"></li>
               </ul>
               ''' % self.emptyList + '</div>'


    def wmfactory_playlists(self, request):
        # Database definition
        select = sqlquery.Select()
        select.addcolumn(remus_playlists_pl_name)
        select.addcolumn(sqlquery.COUNT(remus_plmapping_plm_song))
        group_by = remus_plmapping.relations[remus_playlists]
        sql = select.select(group_by=group_by)

        conn = remus.db_connect.set_current_user(user="root")
        cursor = conn.cursor()
        cursor.execute(sql)

        return [ "%s (%s)" % (name, count) for name, count in cursor ]

resource = Playlist()
