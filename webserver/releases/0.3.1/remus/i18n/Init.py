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

"""Internationalization interface.

This module provides functions to control what language text is
presented as.
"""

__author__ = 'Daniel Larsson, <daniel.larsson@servicefactory.se>'

import gettext
import logging

logger = logging.getLogger("remus.webserver")

_languages = {}

def add_translation(domain, lang, language, locale, icon):
    l = gettext.translation(domain, languages=[lang], fallback=True)
    if not _languages.has_key(domain):
        _languages[domain] = {}
    _languages[domain][lang] = {
        'icon':        icon,
        'language':    language,
        'locale':      locale,
        'translation': l,
        }
    return l


def installed_languages():
    # Returns the union of all domains' installed languages
    languages = {}
    for langinfo in _languages.values():
        for lang, d in langinfo.items():
            languages[lang] = d

    return languages


from twisted.python import components

class ITranslator(components.Interface):
    def setLanguage(self, lang):
        pass

    def langinfo(self):
        pass

    def gettext(self, domain):
        pass


class Translator:

    __implements__ = ITranslator

    def __init__(self, session):
        self.session = session
        self.lang = "en"

    def setLanguage(self, lang):
        self.lang = lang

    def icon(self):
        info = self.languageinfo()
        return info.values()[0]['icon']

    def locale(self):
        info = self.languageinfo()
        return info.values()[0]['locale']        

    def langinfo(self):
        return _languages['remus_server'][self.lang]
    
    def gettext(self, domain):
        info = self.languageinfo()
        trans = info[domain]['translation']

        def _gettext(s):
            "Encode the string as UTF8"
            charset = trans.charset()
            if charset:
                import codecs
                return codecs.getencoder("UTF8")(
                    unicode(trans.gettext(s), charset))[0]
            else:
                return s
        return _gettext

    def languageinfo(self):
        found_translation = False
        info = {}
        for domain in _languages.keys():
            if _languages[domain].has_key(self.lang):
                info[domain] = _languages[domain][self.lang] 
                found_translation = True
            else:
                logger.warning("Domain %s has no '%s' translation",
                               (domain, language))
                info[domain] = {}
                info[domain]["translation"] = gettext.translation(
                    domain, languages=[language],
                    fallback=True)
                
        #import locale
        #locale.setlocale(locale.LC_ALL, get_locale())

        if not found_translation:
            logger.warning("No translations for %s was found", language)
    
        return info

from twisted.web import server
components.registerAdapter(Translator, server.Session, ITranslator)
