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

"""Parses m3u style playlists.

Supports extended m3u playlists.  The format is a simple
text file, with URLs to each song on separate lines.  Extended format
includes information about each song on a separate line before each
URL.  Lines part of the extended format are prefixed by '#EXT'.  Other
lines starting with the character '#' are ignored.
"""

__author__ = "Daniel Larsson <Daniel.Larsson@servicefactory.se>"


import re
import urllib2
import posixpath

m3uinfo_re = re.compile(r"#EXTINF:(?P<length>\d+),(?P<name>.*)")


class Playlist:

    def __init__(self, url):
        self.songs = []

    def add_url(self, url):
        "Get playlist from 'url'"
        file = urllib2.urlopen(url)

        import codecs
        decoder = codecs.getdecoder("UTF8")

        heading = file.readline()
        assert heading.startswith("#EXTM3U")

        for line in file:
            song = song.Song(posixpath.dirname(url),
                             url=file.readline())
            match = m3uinfo_re.match(line)
            if match:
                song.length = int(match.group("length"))
                art_song = match.group("name").split(" - ")
                song.artist = decoder(art_song[0])[0]
                song.title = decoder(" - ".join(art_song[1:]))[0]
                song.audio_type = "audio/mpeg"
                
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
