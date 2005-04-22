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

"""Base class for Remus pages.

Common routines, and subclass of twisted.web.woven.page.Page, to
ensure a common look of remus pages.
"""

import os, sys
import logging
import locale

from twisted.web.woven import page, widgets
from twisted.web import microdom

import remus.i18n
import remus.webserver
import remus.webserver.menu

logger = logging.getLogger("remus.webserver")


def parse(s):
    return microdom.parseString(s, caseInsensitive=0, preserveCase=0)

document = parse("<xml />")

# Create logo
_link = document.createElement("a")
_link.attributes.update({'href': "http://remusic.berlios.de/"})
_link.appendChild(document.createTextNode("&"))
_span = document.createElement("span")
_span.attributes.update({'style': 'color:red'})
_span.appendChild(document.createTextNode("re:"))
_link.appendChild(_span)
del _span
_i = document.createElement("i")
_i.appendChild(document.createTextNode("MUS"))
_link.appendChild(_i)
del _i
_span = document.createElement("span")
_span.attributes.update({'style': 'color:blue'})
_span.appendChild(document.createTextNode("ic"))
_link.appendChild(_span)
del _span
_link.appendChild(document.createTextNode(";"))

LOGO = _link
del _link


class Stylesheet(widgets.Widget):
    tagName = 'link'

    def initialize(self, link=""):
        self.link = link

    def setLink(self, link):
        self.link = link

    def setUp(self, request, node, data):
        href = self.link or data
        self['rel'] = "stylesheet"
        self['type'] = "text/css"
        self['href'] = href


class Generated(widgets.Widget):
    tagName = 'div'

    def setUp(self, request, node, data):
        sess = request.getSession(remus.i18n.ITranslator)
        _ = sess.gettext('remus-server')
        self["class"] = 'generated'
        t = _('Generated at %s by ')
        t = t % self.model.orig['time']
        self.appendChild(document.createTextNode(t))
        self.appendChild(LOGO)
        self.appendChild(document.createTextNode(_(' server at ')))
        link = document.createElement('a')
        link.attributes.update({'href': self.model.orig["baseurl"]})
        link.appendChild(document.createTextNode(self.model.orig["baseurl"]))
        self.appendChild(link)

def remus_page_hierarchy(cls, l=None):
    "Returns a list of inherited classes up to RemusPage"
    if l == None:
        l = []
    if issubclass(cls, RemusPage):
        l.insert(0, cls)
        for base in cls.__bases__:
            remus_page_hierarchy(base, l)
    return l


def get_template(cls):
    if cls.template:
        template = cls.template
    elif cls.templateFile:
        if not cls.templateDirectory:
            mod = sys.modules[cls.__module__]
            if hasattr(mod, '__file__'):
                cls.templateDirectory = os.path.split(mod.__file__)[0]

        template = open(os.path.join(
            cls.templateDirectory, cls.templateFile)).read()
    return template

def merge_templates(cls, template):
    base_template = get_template(cls)
    return base_template.replace("<child/>", template)


class RemusPage(page.Page):

    title = "Remus page"
    
    templateFile = "RemusPage.html"

    templateDirectory = remus.webserver.config.get('server', 'defaultroot')

    def getSubtemplate(self, request):
        if self.template:
            template = self.template
        elif cls.templateFile:
            if not self.templateDirectory:
                mod = sys.modules[cls.__module__]
                if hasattr(mod, '__file__'):
                    self.templateDirectory = os.path.split(mod.__file__)[0]

            template = open(os.path.join(
                self.templateDirectory, self.templateFile)).read()
        return template

    def getTemplate(self, request):
        template = open(os.path.join(
            self.templateDirectory, self.templateFile)).read()
        
        subtemplate = self.getSubtemplate(request)
        template = template.replace("<child/>", subtemplate)

        # Find out what locale the user has selected
        import remus.i18n
        sess = request.getSession(remus.i18n.ITranslator)
        sesslocale = sess.locale()
        locale.setlocale(locale.LC_ALL, sesslocale)

        import time
        self.generated = {
            'time': time.strftime("%X %x"),
            'baseurl': None
            }

        self.menu = remus.webserver.menu.create_basemenu()
        return template

    def wvfactory_Stylesheet(self, request, node, model):
        return Stylesheet(model)

    def wmfactory_title(self, request):
        _ = request.getSession(remus.i18n.ITranslator).gettext('remus-server')
        return _(self.title)

    def wmfactory_stylesheet(self, request):
        return "/styles/toppages.css"

    def wvfactory_Menu(self, request, node, model):
        return remus.webserver.menu.Menu(model)

    def wmfactory_menu(self, request):
        return self.menu

    def wmfactory_generated(self, request):
        from urllib import quote
        inet, addr, port = request.getHost()
        if request.isSecure():
            default = 443
        else:
            default = 80
        if port == default:
            hostport = ''
        else:
            hostport = ':%d' % port
        self.generated['baseurl'] = quote('http%s://%s%s/' % (
            request.isSecure() and 's' or '',
            request.getRequestHostname(),
            hostport), "/:")
        return self.generated

    def wvfactory_Generated(self, request, node, model):
        return Generated(model)
