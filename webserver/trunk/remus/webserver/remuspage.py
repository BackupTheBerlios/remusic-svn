
import os, sys
import logging

from twisted.web.woven import page, widgets
from twisted.web import microdom

import remus.i18n

logger = logging.getLogger("remus.webserver")


def parse(s):
    return microdom.parseString(s, caseInsensitive=0, preserveCase=0)

document = parse("<xml />")

# Create logo
_link = document.createElement("a")
_link.attributes.update({'href': "http://www.remus.org/"})
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


class Menu(widgets.Widget):
    tagName = 'div'
    
    def setUp(self, request, node, data):
        _ = remus.i18n.dgettext('remus-server')
        for menuitem in self.model:
            link = document.createElement("a")
            link.attributes.update({
                'href':  menuitem.orig["link"],
                'title': _(menuitem.orig["tooltip"])})
            if menuitem.orig.has_key('text'):
                link.appendChild(document.createTextNode(_(menuitem.orig["text"])))
            elif menuitem.orig.has_key('element'):
                link.appendChild(menuitem.orig['element'])

            span = document.createElement("span")
            span.attributes.update({
                'class':  "menuitem"})
            span.appendChild(link)
            self.appendChild(span)
            self["class"] = "topmenu"

class Generated(widgets.Widget):
    tagName = 'div'

    def setUp(self, request, node, data):
        _ = remus.i18n.dgettext('remus-server')
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
        l.append(cls)
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

    templateDirectory = "/usr/local/libdata/remus"

    # Fake '_' to make gettext add these strings to the .pot
    # file. Translation is done when actually generating the menu.
    _ = lambda a: a

    _menu = [
        {
            'text': _('Home'),
            'link': '/',
            'tooltip': _('To Remus homepage')
        },
        {
            'text': _('Browse'),
            'link': '/music/',
            'tooltip': _('Browse the music database')
        },
        {
            'text': _('Playlists'),
            'link': '/playlists/',
            'tooltip': _('Manage playlists')
        },
        {
            'text': _('Server statistics'),
            'link': '/stats/',
            'tooltip': _('Various server statistics')
        },
        ]

    del _

    def __init__(self, *args, **kwargs):
        page.Page.__init__(self, *args, **kwargs)

        hier = remus_page_hierarchy(self.__class__)

        template = get_template(self)

        for cls in hier[1:]:
            template = merge_templates(cls, template)
        self.template = template
        import time
        self.generated = {
            'time': time.strftime("%+"),
            'baseurl': None
            }

        # Add languages to the menu
        # FIXME: Change this when I have a better menu code, this
        # should be a popup menu
        self.menu = self._menu[:]
        langinfos = remus.i18n.installed_languages()
        langs = langinfos.keys()
        langs.sort()
        for lang in langs:
            self.menu.append({
                'element': parse('<img width="20pt" src="%s"/>' % langinfos[lang]['icon']),
                'link':    '/lang/?lang=%s' % lang,
                'tooltip': langinfos[lang]['language']
                })

    def wvfactory_Stylesheet(self, request, node, model):
        return Stylesheet(model)

    def wmfactory_title(self, request):
        return self.title

    def wmfactory_stylesheet(self, request):
        return "/styles/remus.css"

    def wvfactory_Menu(self, request, node, model):
        return Menu(model)

    def wmfactory_menu(self, request):
        return self.menu

    def wmfactory_generated(self, request):
        self.generated['baseurl'] = request.prePathURL()
        return self.generated

    def wvfactory_Generated(self, request, node, model):
        return Generated(model)
