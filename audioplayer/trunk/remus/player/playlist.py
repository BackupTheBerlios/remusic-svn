"""Manage playing a playlist, redirecting each audio clip to the
appropriate plugin"""

__author__ = "Daniel Larsson <Daniel.Larsson@servicefactory.se>"


import re
import urllib2
import posixpath

m3uinfo_re = re.compile(r"#EXTINF:(?P<length>\d+),(?P<name>.*)")


class Playlist:

    def __init__(self, url):
        "Get playlist from 'url'"
        file = urllib2.urlopen(url)

        import codecs
        decoder = codecs.getdecoder("UTF8")

        # FIXME: We need a different format than extended m3u
        # playlists, since this is really an mp3 only playlist.
        # For Remus, a proprietary format is ok, since we're in
        # control of both ends, but a more standard format would
        # be nicer.
        #
        # WinAMP 3 has an XML based playlist format. Though it seems
        # fairly WinAMP-centric, an XML format is a decent way of
        # doing it.
        heading = file.readline()
        assert heading == "#EXTM3U\n"

        songs = []
        for line in file:
            song = {}
            song["url"] = posixpath.join(url, file.readline())
            match = m3uinfo_re.match(line)
            if match:
                song["time"] = int(match.group("length"))
                art_song = match.group("name").split(" - ")
                song["artist"] = decoder(art_song[0])[0]
                song["song"] = decoder(" - ".join(art_song[1:]))[0]
                song["mime"] = "audio/mpeg"
                
            songs.append(song)


        self.songs = songs
        self.cursong = 0


    def shuffle(self):
        import random
        random.shuffle(self.songs)


    def __len__(self):
        return len(self.songs)

    def __getitem__(self, ix):
        return self.songs[ix]

    def __iter__(self):
        return self.songs.__iter__()
