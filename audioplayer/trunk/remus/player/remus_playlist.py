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

"""Parses remus style playlists.

Remus playlists support audio clips in multiple formats, and provides
detailed information about each clip.  The playlist is expressed in
XML.
"""

__author__ = "Daniel Larsson <Daniel.Larsson@servicefactory.se>"

import sys, os
import urllib
import xml.sax
import xml.sax.handler

import song


class SAXHandler(xml.sax.handler.ContentHandler):

    def __init__(self, playlist, url):
        self.__pl = playlist
        self.__song = None
        self.__attr_set = None
        self.__baseurl = os.path.dirname(url)
        self.__external_pl = []
        self.__curstr = ''
        
    def startElement(self, name, attrs):
        self.__curstr = ''
        try:
            getattr(self, "start_%s" % name.lower())(attrs)
        except AttributeError:
            if self.__song:
                try:
                    self.__attr_set = self.__song.setter(name)
                except AssertionError:
                    pass

    def endElement(self, name):
        self.__curstr = self.__curstr.strip()
        if self.__attr_set and self.__curstr:
            self.__attr_set(self.__curstr)
            self.__curstr = ''
        try:
            getattr(self, "end_%s" % name.lower())()
        except AttributeError:
            pass

    def characters(self, s):
        self.__curstr += s

    def start_song(self, attrs):
        assert not self.__song
        self.__song = song.Song(self.__baseurl)

    def end_song(self):
        assert self.__song
        self.__pl.add_song(self.__song)
        self.__song = None

    def start_playlist(self, attrs):
        if attrs.has_key(u'href'):
            self.__external_pl.append(attrs[u'href'])

    def endDocument(self):
        for pl in self.__external_pl:
            self.__pl.add_uri(os.path.join(self.__baseurl, pl))


class Playlist(object):
    def __init__(self):
        self.songs = []

    def add_url(self, uri):
        xml.sax.parse(uri, SAXHandler(self, uri))

    def add_song(self, song):
        self.songs.append(song)

    def shuffle(self):
        import random
        random.shuffle(self.songs)

    def __len__(self):
        return len(self.songs)

    def __getitem__(self, ix):
        return self.songs[ix]

    def __iter__(self):
        return self.songs.__iter__()


if __name__ == '__main__':
    pl = Playlist()
    pl.add_url("http://127.0.0.1/music/search/baader/list/remus")
    for song in pl.songs:
        print song.__dict__
