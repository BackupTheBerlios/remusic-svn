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

"""Audio player.

Plays audio files using the gstreamer framework.
"""

__author__ = "Daniel Larsson <Daniel.Larsson@servicefactory.se>"

import time
import gstreamer
import gtk
import remus_playlist

STATE = {
    gstreamer.STATE_NULL:    'null',
    gstreamer.STATE_PAUSED:  'paused',
    gstreamer.STATE_PLAYING: 'playing',
    gstreamer.STATE_READY:   'ready',
    gstreamer.STATE_FAILURE: 'failure',
    }

def entry_to_python(entry):
    name = entry.get_name()
    type = entry.get_props_type()

    if type == gstreamer.PROPS_INT_TYPE:
        ret, val = entry.get_int()
    elif type == gstreamer.PROPS_FLOAT_TYPE:
        ret, val = entry.get_float()
    elif type == gstreamer.PROPS_FOURCC_TYPE:
        ret, val = entry.get_fourcc()
    elif type == gstreamer.PROPS_BOOLEAN_TYPE:
        ret, val = entry.get_bool()
    elif type == gstreamer.PROPS_STRING_TYPE:
        ret, val = entry.get_string()
    elif type == gstreamer.PROPS_INT_RANGE_TYPE:
        ret, min, max = entry.get_int_range()
        val = (min, max)
    elif type == gstreamer.PROPS_FLOAT_RANGE_TYPE:
        ret, min, max = entry.get_float_range()
        val = (min, max)
    elif type == gstreamer.PROPS_LIST_TYPE:
        ret, _val = entry.get_list()
        val = [ entry_to_python(e) for e in _val ]
    else:
        print '%sWARNING: %s: unknown property type %d' % (indent, name, type)
    assert ret
    return name, type, val

class Player(object):
    def __init__(self):
        self.playlist = remus_playlist.Playlist()
        self.cursong = 0
        self.__eof = True
        self.__idle = None
        self.__timeout = None
        self.make_pipeline()

    def props(self, caps):
        props = caps.get_props()
        ret, plist = props.get_list()
        elems = {}
        for entry in plist:
            name, type, val = entry_to_python(entry)
            elems[name] = val
        return elems
    
    def streaminfo(self, props):
        pass

    def metadata(self, props):
        pass
        
    def decoder_notified(self, sender, pspec):
        caps = sender.get_property(pspec.name)
        props = self.props(caps)
        if pspec.name == 'streaminfo':
            self.streaminfo(props)
        elif pspec.name == 'metadata':
            self.metadata(props)
        else:
            print 'notify:', sender, pspec

    def make_pipeline(self):
        # create a new bin to hold the elements
        self.__bin = gstreamer.Pipeline('pipeline')
        self.__bin.connect('state_change', self.__state_change)

        # create a disk reader
        filesrc = gstreamer.gst_element_factory_make ('gnomevfssrc', 'vfs_source')
        if not filesrc:
            print 'could not find plugin "gnomevfssrc"'
            return -1
        self.__filesrc = filesrc
        filesrc.connect('eos',self.eof)

        # now get the decoder
        decoder = gstreamer.gst_element_factory_make ('mad', 'parse')
        if not decoder:
            print 'could not find plugin "mad"'
            return -1
        decoder.connect('notify', self.decoder_notified)
        
        # and an audio sink
        osssink = gstreamer.gst_element_factory_make ('osssink', 'play_audio')
        if not osssink:
            print 'could not find plugin "osssink"'
            return -1
        
        #  add objects to the main pipeline
        for e in (filesrc, decoder, osssink):
            self.__bin.add(e)
            
        # link the elements
        previous = None
        for e in (filesrc, decoder, osssink):
            if previous:
                previous.link(e)
            previous = e

    def eof(self, sender):
        self.__eof = True
        self.cursong += 1
        self.stop()

    def quit(self):
        self.stop()
        gtk.main_quit()

    def state(self):
        return STATE[self.__bin.get_state()]

    def pause(self):
        if self.__bin.get_state() == gstreamer.STATE_PAUSED:
            self.__bin.set_state(gstreamer.STATE_PLAYING)
        else:
            self.__bin.set_state(gstreamer.STATE_PAUSED)

    def play(self):
        if self.cursong >= len(self.playlist):
            self.quit()
            return
        else:
            if not self.__filesrc.get_property('location'):
                self.__filesrc.set_property('location',
                                            self.playlist[self.cursong].geturl())
            
        self.__bin.set_state(gstreamer.STATE_PLAYING)

    def stop(self):
        self.__bin.set_state(gstreamer.STATE_NULL)
        self.__filesrc.set_property('location', None)

    def start(self):
        self.play()
        gtk.main()

    def idle(self, *arg):
        if not self.__bin.iterate() and self.__eof:
            self.__eof = False
            self.play()
            
        return self.__bin.get_state() == gstreamer.STATE_PLAYING

    def __state_change(self, sender, oldstate, newstate):
        if newstate == gstreamer.STATE_PLAYING:
            if self.__idle:
                gtk.idle_remove(self.__idle)
                gtk.timeout_remove(self.__timeout)
            self.__idle = gtk.idle_add(self.idle, None)
            self.__timeout = gtk.timeout_add(200, self.time_tick)

    def time_tick(self, *args):
        clock = self.__bin.get_clock()
        time_nanos = clock.get_time()
        secs = time_nanos / 1000000000.0
        self.elapsed_time(secs)
        return self.__bin.get_state() == gstreamer.STATE_PLAYING

if __name__ == "__main__":
    class TestPlayer(Player):
        def elapsed_time(self, secs):
            print 't', secs

        def play(self):
            super(TestPlayer, self).play()
            song = self.playlist[self.cursong]

            print "S", song.title
            print "A", song.artist
            print "T", song.length

        
    p = TestPlayer()
    p.make_pipeline()
    p.playlist.add_url('http://127.0.0.1/music/list/remus')
    p.playlist.shuffle()
    p.start()
