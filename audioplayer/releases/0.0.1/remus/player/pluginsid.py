"""SID plugin for the Remus player."""

__author__ = "Daniel Larsson <Daniel.Larsson@servicefactory.se>"


import os
import re
import asyncore
import audioplugin
import logging

logger = logging.getLogger("remus.player.sid")


class sidplay_wrapper(asyncore.file_dispatcher):
    def __init__(self, plugin, file):
        pass

class sid_plugin(audioplugin.plugin):
    def __init__(self, player):
        """Create the SID player plugin, with a reference to
        the player framework"""

        audioplugin.plugin.__init__(self, player)

        # Are we ready to play files?
        self.ready = True


    # Methods inherited from audioplugin.player

    def play(self, url):
        "Play new song"
        
        self.mp3ctrl.write("LOAD %s\n" % url)
        self.mp3ctrl.flush()
        
        
    def stop(self):
        "Stop playing song"
        self.mp3ctrl.write("STOP\n")
        self.mp3ctrl.flush()


    def pause(self):
        "Pause player"
        self.mp3ctrl.write("PAUSE\n")
        self.mp3ctrl.flush()

    def fast_forward(self, nrframes):
        "Fast forward 'nrframes' number of frames."
        self.mp3ctrl.write("JUMP +%d\n" % nrframes)
        self.mp3ctrl.flush()

    def fast_backward(self, nrframes):
        "Fast backward 'nrframes' number of frames."
        self.mp3ctrl.write("JUMP -%d\n" % nrframes)
        self.mp3ctrl.flush()

    # Methods inherited from asyncore.file_dispatcher
        
    def writable(self):
        # We're listening for input, not writing here
        return False

    def close(self):
        # Send quit to mpg123
        if self.mp3ctrl:
            self.mp3ctrl.write("QUIT\n")
            self.mp3ctrl.flush()
            import time
            time.sleep(1)
            self.del_channel()
            self.mp3ctrl = None

    def handle_close(self):
        self.close()

    def handle_error(self):
        logger.error("Error from mpg123")
        raise

    def handle_read(self):
        # mpg123 wrote to stdout!

        info = self.socket.read(100)

        # Read one line at a time, so make sure we have gotten
        # one or more complete lines, saving any partly read
        # line in 'self.curline' for next batch of input.
        # We need to prepend any previously recieved data
        # to the first line as well
        lines = info.split("\n")
        lines[0] = self.curline + lines[0]
        self.curline = ''
        if lines[-1] != '':
            self.curline = lines[-1]

        # Last line is either incomplete, or empty, so remove it
        # from the set of lines to process
        del lines[-1]

        pl = self.player

        for line in lines:
            if line.startswith("@R MPG123"):
                # mpg123 init string
                self.ready = True
                pl.ready(self)
                
            elif line.startswith("@F"):
                # Frame information
                match = frameinfo_re.match(line)
                if match:
                    time = float(match.group("time"))
                    pl.elapsed_time(self, time)
                else:
                    logger.warning("Mysterious format in frame message: %s (%s)",
                                   line, frameinfo_re.pattern)

            elif line.startswith("@P 0"):
                # Playing stopped
                pl.status(self, audioplugin.PLAY_STOPPED)

            elif line.startswith("@P 1"):
                # Playing paused
                pl.status(self, audioplugin.PLAY_PAUSED)

            elif line.startswith("@P 2"):
                # Playing resumed
                pl.status(self, audioplugin.PLAY_RESUMED)

            elif line.startswith("@S"):
                # Stream info
                # @S 1.0 3 44100 Joint-Stereo 2 417 2 0 0 0 128 0
                version, layer, freq, mode, _, _, _, _, _, _, rate, _ = \
                         line.split()[1:]

                pl.streaminfo(self, "MPEG %s %s, %s kbit/s, %s Hz %s" % \
                              (version, "I" * int(layer), rate, freq, mode))

            elif line.startswith("@I"):
                # ID3 or filename info
                pass

            elif line.startswith("@E"):
                pl.plugin_error(self, line[3:])
                
            else:
                logger.warning("Unhandled input: %s", line)


audioplugin.register("audio/mpeg", mpg123_plugin)
