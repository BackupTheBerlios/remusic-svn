
import os, sys
import gettext

from twisted.web.woven import page, widgets
from twisted.web import microdom

t = gettext.translation(
    'remusserver', '/usr/local/share/locale', fallback=True)
_ = t.gettext

document = microdom.parseString("<xml />", caseInsensitive=0, preserveCase=0)


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
        for menuitem in self.model:
            link = document.createElement("a")
            link.attributes.update({
                'href':  menuitem.orig["link"],
                'title': menuitem.orig["tooltip"]})
            link.appendChild(document.createTextNode(menuitem.orig["text"]))

            span = document.createElement("span")
            span.attributes.update({
                'class':  "menuitem"})
            span.appendChild(link)
            self.appendChild(span)
            self["class"] = "topmenu"

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

    menu = (
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
        }
        )

    def __init__(self, *args, **kwargs):
        page.Page.__init__(self, *args, **kwargs)

        hier = remus_page_hierarchy(self.__class__)

        template = get_template(self)

        for cls in hier[1:]:
            template = merge_templates(cls, template)
        self.template = template

    def wvfactory_Stylesheet(self, request, node, model):
        return Stylesheet(model)

    def wmfactory_base_url(self, request):
        return request.prePathURL()

    def wmfactory_title(self, request):
        return self.title

    def wmfactory_stylesheet(self, request):
        return "/styles/remus.css"

    def wvfactory_Menu(self, request, node, model):
        return Menu(model)

    def wmfactory_menu(self, request):
        return self.menu
