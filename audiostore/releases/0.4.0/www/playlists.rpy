# -*- mode: python -*-

import sqlquery

import remus.db_connect
import remus.webserver.remuspage
from remus.audiostore.db_audiostore import *
import remus.i18n
_ = remus.i18n.dgettext('remus-audiostore')


class Playlist(remus.webserver.remuspage.RemusPage):

    title = _("Playlist administration")

    emptyList = _("No playlists defined")
    template = '<div class="text">' + \
               _("Defined playlists:") + \
               '''<ul model="playlists" view="List">
               <li pattern="emptyList">%s</li>
               <li pattern="listItem" view="Text"></li>
               </ul>
               ''' % emptyList + \
    '</div>'


    def wmfactory_playlists(self, request):
        # Database definition
        select = sqlquery.Select()
        select.addcolumn(remus_playlists_pl_name)
        select.addcolumn(sqlquery.COUNT(remus_plmapping_plm_song))
        group_by = remus_plmapping.relations[remus_playlists]
        sql, args = select.select(group_by=group_by)

        conn = remus.db_connect.set_current_user(user="root")
        cursor = conn.cursor()
        cursor.execute(sql, args)

        return [ "%s (%s)" % (name, count) for name, count in cursor ]

resource = Playlist()
