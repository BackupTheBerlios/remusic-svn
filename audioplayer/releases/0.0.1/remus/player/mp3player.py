"""MP3 plugin for the Remus player."""

__author__ = "Daniel Larsson <Daniel.Larsson@servicefactory.se>"


import os
import re
import asyncore
import audioplugin
import logging

logger = logging.getLogger("remus.player.mp3")


frameinfo_re = re.compile(
    r"@F"                      # Frame information string
    r"(?P<frame>\d+) "         # Frame number
    r"(?P<frameleft>\d+) "     # Frames left in stream (possibly 0)
    r"(?P<time>\d+\.\d+) "     # Elapsed time
    r"(?P<timeleft>\d+\.\d+)"  # Remaining time (possibly 0.0)
    )


class mpg123_player(audioplugin.plugin, asyncore.file_dispatcher):
    def __init__(self, player):
        """Create the mp3 player plugin, with a reference to
        the player framework"""

        audioplugin.plugin.__init__(self, player)

        # Start the mpg123 worker process in 'remote' mode
        pout, pin = os.popen4("mpg123 -R foo", "t")

        # Listen to stdout activity from mpg123 (our 'pin' is
        # mpg123's stdout)
        asyncore.file_dispatcher.__init__(self, pin.fileno())

        self.mp3ctrl = pout

        # Are we ready to play files? (not yet, need to recieve the
        # startup command string from mpg123)
        self.ready = False

        # Partly received lines saved here
        self.curline = ''


    # Methods inherited from audioplugin.player

    def stop(self):
        "Stop playing song"
        self.outp.write("STOP\n")
        self.outp.flush()


    def pause(self):
        "Pause player"
        self.outp.write("PAUSE\n")
        self.outp.flush()


    # Methods inherited from asyncore.file_dispatcher
        
    def writable(self):
        # We're listening for input, not writing here
        return False


    def handle_close(self):
        # Send quit to mpg123
        self.player.write("QUIT")
        self.player.flush()
        self.close()


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
                
            elif line.startswith("@F"):
                # Frame information
                match = frameinfo_re.match(line)
                if match:
                    time = float(match.group("time"))
                    pl.elapsed_time(self, time)
                else:
                    logger.warning("Mysterious format in frame message: %s",
                                   line)

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

