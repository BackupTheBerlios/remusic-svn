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

"""Main remus menu.

The main menu appears on many remus pages, but the exact contents
depend on what modules are installed.
"""

__author__ = 'Daniel Larsson, <daniel.larsson@servicefactory.se>'

from twisted.web import microdom
from twisted.web.woven import model
from twisted.web.woven import widgets

import remus.i18n


def parse(s):
    return microdom.parseString(s, caseInsensitive=0, preserveCase=0)

document = parse("<xml />")


class MenuModel(model.Model):
    def initialize(self, *args, **kwargs):
        self.icon = kwargs.get("icon")
        self.iconsize = kwargs.get("iconsize")
        self.name = kwargs.get("name", '')
        self.title = kwargs.get("title", '')
        self.desc = kwargs.get("description", '')
        self.basemenu = kwargs.get("basemenu")
        self.menues = kwargs.get("menu", [])
        self.align_right = []
        self.url = None

    def add_menu(self, menu, after=None, align_right=None):
        assert not (after and align_right)
        if after:
            self.menues.insert(self.menues.index(after)+1, menu)
        else:
            self.menues.append(menu)
            if align_right:
                self.align_right.append(menu)


class MenuItem(MenuModel):
    def initialize(self, *args, **kwargs):
        MenuModel.initialize(self, *args, **kwargs)
        self.url = kwargs.get("url")


def create_basemenu():
    # The base menu, which should be present on all pages
    _ = lambda a: a

    langinfo = remus.i18n.installed_languages()
    langs = langinfo.keys()
    langs.sort()

    languages = [ MenuItem(icon=langinfo[lang]['icon'],
                           iconsize=20,
                           title=langinfo[lang]['language'],
                           url="/lang/?lang=%s" % lang)
                  for lang in langinfo.keys() ]
    
    basemenu = MenuModel(name="topmenu")
    basemenu.add_menu(
        MenuItem(name="home", title=_("Home"),
                 description=_("To Remus homepage"), url="/"))
    basemenu.add_menu(
        MenuItem(name="music", title=_("Music"),
                 description=_("Browse the music database"), url="/music/"))
    basemenu.add_menu(
        MenuItem(name="playlists", title=_("Playlists"),
                 description=_("Manage playlists"), url="/playlists/"))
    basemenu.add_menu(
        MenuItem(name="stats", title=_("Statistics"),
                 description=_("Various server statistics"), url="/stats/"))
    basemenu.add_menu(
        MenuModel(name="lang", title=_("Language"),
                  description=_("Select language"),
                  menu=languages))

    documents = MenuModel(name="docs", title=_("Documents"),
                  description=_("Available documents"))
    basemenu.add_menu(documents)

    # This does not belong here, it's an 'audiostore' item and should
    # be installed by that package.  I don't support installation of
    # package specific global menues yet though.
    documents.add_menu(
        MenuItem(name="manual", title=_("Audiostore Manual"),
                 description=_("The audiostore manual"), url="/manual/"))

    return basemenu


from types import StringTypes, UnicodeType

class RawText(microdom.CharacterData):
    def writexml(self, stream, indent='', addindent='', newl='', strip=0, nsprefixes={}, namespace=''):
        val = self.data
        if isinstance(val, UnicodeType):
            val = val.encode('utf8')
        stream.write(val)


class Menu(widgets.Widget):
    """HTML extensible menu"""

    tagName = 'div'
    
    def setUp(self, request, node, data):

        _ = request.getSession(remus.i18n.ITranslator).gettext('remus-server')

        self["id"] = self.model.name
        self["class"] = "topmenu"

        for menuitem in self.model.menues:
            span = document.createElement("span")
            self.appendChild(span)
            span.attributes.update({
                "class"      : "menuitem",
                "onmouseover": "menu.openMenu(this)",
                })
            
            if menuitem.name:
                span.attributes.update({"id":menuitem.name})

            if menuitem.url:
                link = document.createElement("a")
                link.attributes.update({'href':  menuitem.url})
                if menuitem.desc:
                    link.attributes.update({'title': _(menuitem.desc)})
                link.appendChild(document.createTextNode(_(menuitem.title)))

                span.appendChild(link)
            else:
                span.appendChild(document.createTextNode(_(menuitem.title)))

            if menuitem.menues:
                submenu = document.createElement("div")
                submenu.attributes.update({
                    "id"    : "%s_menu" % menuitem.name,
                    "class" : "menu",
                    })

                for item in menuitem.menues:
                    div = document.createElement("div")
                    div.attributes.update({"class": "menuitem"})

                    link = document.createElement("a")
                    link.attributes.update({'href':  item.url})
                    if item.desc:
                        link.attributes.update({'title': _(item.desc)})

                    if item.icon:
                        img = document.createElement("img")
                        img.attributes.update({
                            'alt'    : '[icon]',
                            'border' : "0",
                            'align'  : "middle",
                            'src'    : item.icon})
                        if item.iconsize:
                            img.attributes.update(
                                {'width' : str(item.iconsize)})

                        link.appendChild(img)
                        link.appendChild(document.createTextNode(" "))

                    link.appendChild(document.createTextNode(_(item.title)))

                    div.appendChild(link)
                    submenu.appendChild(div)

                self.appendChild(submenu)

        # Add init code
        script = document.createElement("script")
        script.attributes.update({
            "type"    : "text/javascript",
            "language": "JavaScript",
            })
        script.appendChild(RawText(
            '\nvar menu = new RemusMenu(document.getElementById("%s"));' % self.model.name))
        self.appendChild(script)

