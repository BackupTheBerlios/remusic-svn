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

"""Information about a song.

Keeps information about a song.  Instances of this class is created by
the playlist classes, and filled in with whatever information is part
of the particular playlist format.  Several of these attributes may be
'None'.
"""

__author__ = "Daniel Larsson <Daniel.Larsson@servicefactory.se>"

import posixpath

class Song(object):
    def __init__(self, baseurl, **kw):
        "Initialize song instance."
        self.baseurl = baseurl
        self.url = kw.get('url', None)
        self.title = kw.get('title', None)
        self.artist = kw.get('artist', None)
        self.album = kw.get('album', None)
        self.audio_type = kw.get('audio_type', None)
        self.audio_mode = kw.get('audio_mode', None)
        self.length = kw.get('length', None)

    def geturl(self):
        "Get the URL of this song."
        return posixpath.join(self.baseurl, self.url)

    def set_length(self, value):
        self.length = int(value)
        
    def setter(self, attr):
        "Returns a function to set attribute 'attr'."
        # Force exception if attr isn't valid
        getattr(self, attr)
        if attr == 'length':
            return self.set_length
        return lambda val, s=self, attr=attr: setattr(s, attr, val)
