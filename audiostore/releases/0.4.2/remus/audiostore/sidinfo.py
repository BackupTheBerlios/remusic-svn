"""Read SID tune metadata.
"""

import types
import struct

class SIDtune:
#
    def __init__(self, file):
        if type(file) in types.StringTypes:
            self.file = open(file, 'rb')
        else:
            self.file = file
#
        self._parse()
#
    def _parse(self):
        header = self.file.read(4)
        assert header in ("PSID", "RSID")
#
        sidformat = ">hhhhhhhi32s32s32s"
        (self.version,
         _,
         _,
         _,
         _,
         self.songs,
         self.startsong,
         _,
         self.name,
         self.author,
         self.copyright) = struct.unpack(sidformat, file.read(struct.calcsize(sidformat)))
        self.name = self.name.replace("\0", "")
        self.author = self.name.replace("\0", "")
        self.copyright = self.name.replace("\0", "")
