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
_curtranslations = {}
_curlanguage = None
lang = None

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

def install(language):
    global lang
    global _curlanguage

    # Update every domain
    found_translation = False
    for domain in _languages.keys():
        if _languages[domain].has_key(language):
            lang = language
            _curlanguage = _languages[domain][lang] 
            translation = _curlanguage['translation']
            found_translation = True
        else:
            logger.warning("Domain %s has no '%s' translation",
                           (domain, language))
            translation = gettext.translation(domain, languages=[language],
                                              fallback=True)

        _curtranslations[domain] = translation

    import locale
    locale.setlocale(locale.LC_ALL, get_locale())
    if not found_translation:
        logger.warning("No translations for %s was found", language)


def translation(domain):
    return _curtranslations[domain]

def dgettext(domain):
    return translation(domain).gettext

def get_langinfo():
    return _curlanguage

def get_icon():
    if _curlanguage:
        return _curlanguage["icon"]
    else:
        return None

def get_locale():
    if _curlanguage:
        return _curlanguage["locale"]
    else:
        return 'C'

def installed_languages():
    # Returns the union of all domains' installed languages
    languages = {}
    for langinfo in _languages.values():
        for lang, d in langinfo.items():
            languages[lang] = d

    return languages
