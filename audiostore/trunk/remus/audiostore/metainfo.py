"""Extract metainformation from music files.

Extract metainformation from ID3 tags, musicbrainz, or whatever means
we can find.
"""

import logging
import RDF

import remus
import remus.audiostore.remus_mb as remus_mb

from remus.audiostore import config_defaults

from remus.audiostore.storage \
     import xsd, rdf, dc, mm, mq, rem, remtrack

musicbrainz_trmuri = "http://musicbrainz.org/mm-2.1/trmid/"

logger = logging.getLogger("remus.audiostore.storage")


_boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
                   '0': False, 'no': False, 'false': False, 'off': False}

def getboolean(config, section, option, vars=None):
    v = config.get(section, option, vars=vars)
    if v.lower() not in _boolean_states:
        raise ValueError, 'Not a boolean: %s' % v
    return _boolean_states[v.lower()]



USE_MB = getboolean(remus.config, 'autotagger', 'use-musicbrainz',
                    vars=config_defaults)


# ---  Some utility functions

def mime_type(filename):
    import commands
    out = commands.getoutput('file -bi "%s"' % filename)
    return out.strip()

# --- End utility functions


def update_metainfo(filename, info, model=None):
    """Update metainfo about a music file.

    Updates metainfo about the file 'filename'. Metainfo is both
    stored in tags in the file, i.e. as ID3 tags in MP3 files, and
    optionally in an RDF model.

    The RDF model is mainly populated from musicbrainz query results,
    but some additional metadata is stored as well (mostly for
    internal use, such as where in the file system the file is
    stored).

    Parameters:

      filename - filename of file to get metainfo about

      info - dictionary with simple metainfo. Typically pass an empty
      dictionary.

      model - an RDF model to consult and update
    """
    mime = mime_type(filename)
    mf = mime_map[mime](filename)

    # Extract info from ID3 tags and the like
    mf.read(info)

    update_file_and_model(mf, info, model)
    return mf


def update_file_and_model(musicfile, info, model=None):
    """Update metainformation about the given song.

    Unless the musicbrainz acoustic fingerprint is stored in the tag
    information of this song, we compute it (if possible) and ask
    musicbrainz to give us metainformation about it.

    If a unique match is found, and the returned information doesn't
    deviate too much (*) from the information already stored in the
    tag, update tag with musicbrainz info.

    If multiple matches are returned, store this fact in the model so
    the user can manually pick the correct song later.

    Finally, store information about the song in the RDF model,
    whether it's from musicbrainz or from tags.

    Parameters:
      musicfile  - a MusicFile instance
      info       - dictionary with metadata. Can contain info from ID3
                   tags or similar. Will be updated with info from
                   musicbrainz.
      model      - RDF model to insert musicbrainz metadata into.
    """

    # If track already has a TRM (acoustic fingerprint) computed, use
    # that
    trm = info.get('mb_trm_id', None)

    if not trm:

        # Try compute the trm
        try:
            logger.info("Computing TRM for %s", musicfile.filename)
            trm = musicfile.get_trm()
        except NotImplemented:
            pass

    mbtrack = None
    matches = 0    # Musicbrainz matches
    
    # If we have the TRM now, lets go ask musicbrainz for metainfo
    if trm and USE_MB:

        info['mb_trm_id'] = trm
        
        # Do we know anything about this song already?
        trmuri = musicbrainz_trmuri + trm
        trm_stmnt = RDF.Statement(None, None, RDF.Node(uri_string=trmuri))
        print "Looking for statement with object =", trmuri
    
        if model != None and not model.find_statements(trm_stmnt).end():
            # Yes we do, complain for now
            #raise IOError("Already exists")
            pass

        matches, queryresult = remus_mb.get_info(trm, info)

        if queryresult:
            # Returns 'None' if update rejected
            mbtrack = remus_mb.update(musicfile, info, queryresult, model)


    # Insert file into model, or update it if already present
    # (i.e. mbtrack != None)
    track = insert_file(musicfile, info, model, mbtrack)

    if mbtrack is None and model != None:
        # No unique match, so either we got multiple matches, no
        # matches, or the match wasn't close enough to the tag info
        if matches == 1:
            # Seems we got a false match, store it as 0 matches in DB
            matches = 0

        # This track got 'n' matches on musicbrainz
        statement = RDF.Statement(
            track,
            rem.queryMatch,
            RDF.Node(literal=str(matches),
                     datatype=xsd.nonNegativeInteger.uri))
        model.append(statement)

    # Update tag info in file
    musicfile.update(info)


def insert_file(musicfile, info, model, track=None):
    """Insert file into model.

    Adds statements about the musicfile into the model, or, if track
    is non null (i.e. a node in the model), adds remus specific
    statements about it.
    """

    if model is None:
        return

    if not track:
        # For resolved tracks, the URI is the musicbrainz URI. Since
        # we don't have a musicbrainz URI in this case, we make our
        # own from the filename.  This is generated by remus, and is
        # unique.
        #
        # FIXME! It's unique within a server instance, so it should
        # use this server's URI as the base!

        # This is a track
        track = remtrack[musicfile.filename]
        statement = RDF.Statement(track, rdf.type, mm.Track)
        model.append(statement)

    # The track is stored in file ...
    statement = RDF.Statement(track, rem.filename, musicfile.filename)
    model.append(statement)

    # Insert genre information
    for genre in info.get('genre', []):
        statement = RDF.Statement(track, rem.genre, genre)
        model.append(statement)
        
    return track



def get_trm(ff):
    import musicbrainz
    info = ff.info()
    trm = musicbrainz.trm()
    trm.SetPCMDataInfo(info.rate, info.channels, 16)
    while 1:
        (buff, bytes, bit) = ff.read()
        if bytes == 0:
            break
        if trm.GenerateSignature(buff):
            break
        
    return trm.FinalizeSignature()


class MusicFile:
    def __init__(self, filename):
        self.filename = filename

    def get_trm(self):
        """Compute the musicbrainz TRM signature"""
        raise NotImplemented

    def read(self, metainfo):
        """Fill in meta information in the 'metainfo' dictionary."""
        raise NotImplemented

    def update(self, metainfo):
        """Update internal tags with metainfo"""
        raise NotImplemented



# ------------------------------------------------------------
# MP3
# ------------------------------------------------------------

try:
    import mad
    
    class AudioInfo:
        def __init__(self, rate, channels):
            self.rate = rate
            self.channels = channels

    class MadWrapper:
        """
        Make the mad module act more like ogg.vorbis.VorbisFile
        """
        def __init__(self, filename):
            self.ff = mad.MadFile(filename)
    
        def read(self):
            """
            These docs are from ogg.vorbis.VorbisFile.read()
        
            @returns: Returns a tuple: (x,y,z) where x is a buffer
            object of the data read, y is the number of bytes read,
            and z is whatever the bitstream value means (no clue).

            @returntype: tuple
            """
            buff = self.ff.read()
            if buff:
                return (buff, len(buff), None)
            else:
                return ('', 0, None)
            
        def info(self):
            if self.ff.mode() == mad.MODE_SINGLE_CHANNEL:
                channels = 1
            else:
                channels = 2
            return AudioInfo(self.ff.samplerate(), channels)

except ImportError:
    pass


import mmpython.audio.eyeD3

class UFIDFrame(mmpython.audio.eyeD3.Frame):

    header = mmpython.audio.eyeD3.FrameHeader()
    header.id = "UFID"

    # Data string format:
    # owner id + '\x00' + identifier;
    def __init__(self, data, header=None):
        self.set(data, header)

    # Data string format:
    # owner id + '\x00' + identifier;
    def set(self, data, header):
        self.header = header or self.header
        data = self.disassembleFrame(data)
        val = data.split('\x00')
        self.ownerid = self.id = ""
        try:
            self.ownerid = val[0]
            self.id = val[1]
        except IndexError:
            pass

    def __repr__(self):
        return '<%s (%s): %s/%s>' % (self.getFrameDesc(), self.header.id,
                                     self.ownerid, self.id)

    def render(self):
        data = self.ownerid + '\x00' + self.id
        return self.assembleFrame(data)


class MP3MusicFile(MusicFile):

    # Based on information at
    # http://www.musicbrainz.org/docs/specs/metadata_tags.html

    # 
    MB_OWNER_ID = "http://musicbrainz.org"
    MB_ARTIST_ID = "MusicBrainz Artist Id"
    MB_ALBUM_ID = "MusicBrainz Album Id"
    MB_ALBUM_ARTIST_ID = "MusicBrainz Album Artist Id"
    MB_TRM_ID = "MusicBrainz TRM Id"

    # The "Various artists" identifier
    MB_VARIOUS_ARTISTS = "89ad4ac3-39f7-470e-963a-56509c546377"

    TXXX_FIELD_MAP = {
        MB_ARTIST_ID:      'mb_artist_id',
        MB_ALBUM_ID:       'mb_album_id',
        MB_ALBUM_ARTIST_ID:'mb_album_artist_id',
        MB_TRM_ID:         'mb_trm_id',
        }

    # This method is lacking from mmpython.audio.eyeD3.frame.FrameSet
    def setUserTextFrame(self, frameset, frameId, description, text,
                         encoding = mmpython.audio.eyeD3.DEFAULT_ENCODING):
        if not mmpython.audio.eyeD3.USERTEXT_FRAME_RX.match(frameId):
            raise mmpython.audio.eyeD3.FrameException("Invalid Frame ID: " + frameId);

        found = False
        for f in frameset[frameId]:
            if f.description == description:
                f.encoding = encoding
                f.text = text
                found = True

        if not found:
            h = mmpython.audio.eyeD3.FrameHeader(frameset.tagHeader)
            h.id = frameId
            frameset.addFrame(mmpython.audio.eyeD3.createFrame(
                h, encoding + description + '\x00' + text))

    # This method is lacking from mmpython.audio.eyeD3.frame.FrameSet
    def setUFID(self, frameset, owner, id,
                encoding = mmpython.audio.eyeD3.DEFAULT_ENCODING):
        found = False
        for f in frameset["UFID"]:
            ufid = UFIDFrame(f.data, f.header)
            if ufid.ownerid == owner:
                f.data = owner + '\x00' + id
                found = True

        if not found:
            h = mmpython.audio.eyeD3.FrameHeader(frameset.tagHeader)
            h.id = "UFID"
            frameset.addFrame(UFIDFrame(owner + '\x00' + id, h))


    def get_trm(self):
        ff = MadWrapper(self.filename)
        return get_trm(ff)

    def read(self, metainfo):
        import mmpython
        try:
            minfo = mmpython.parse(self.filename)
        except TypeError:
            logger.exception("MP3 tag parse error")

        try:
            if minfo.title:
                metainfo["title"] = minfo.title
            if minfo.genre:
                if metainfo.has_key('genre'):
                    metainfo["genre"].append(minfo.genre)
                else:
                    metainfo["genre"] = [minfo.genre]
            if minfo.date:
                metainfo["year"] = minfo.date
            if minfo.trackno:
                metainfo["tracknr"] = minfo.trackno
            if minfo.album:
                metainfo["album"] = minfo.album
            if minfo.artist:
                metainfo["artist"] = minfo.artist
            if minfo.length:
                metainfo["length"] = "00:%02d:%02d" % \
                                     (minfo.length / 60, minfo.length % 60)
        except:
            pass

        file = mmpython.audio.eyeD3.Mp3AudioFile(self.filename)
        metainfo["bitrate"] = file.getBitRateString()
        metainfo["samplefreq"] = file.header.sampleFreq
        metainfo["audio_mode"] = file.header.mode
        metainfo["subtype"] = "MPEG %s layer %s" % (file.header.version,
                                                    'I' * file.header.layer)

        # Try get musicbrainz tags out of the file
        from mmpython.audio.eyeD3.frames import \
             UserTextFrame, DateFrame

        for frame in file.tag.frames:
            print "Found frame id", frame.header.id
            if frame.header.id == "TXXX":
                print "TXXX:%s" % frame.description
                if self.TXXX_FIELD_MAP.has_key(frame.description):
                    metainfo[self.TXXX_FIELD_MAP[frame.description]] = frame.text
            elif frame.header.id == "TSOP":
                metainfo["artist_sortname"] = frame.text
            elif frame.header.id == "UFID":
                ufid = UFIDFrame(frame.data, frame.header)
                metainfo["mb_track_id"] = ufid.id
                
                
        logger.info(str(metainfo))
        return metainfo


    def update(self, metainfo):
        import codecs
        file = mmpython.audio.eyeD3.Mp3AudioFile(self.filename)

        enc = codecs.getencoder("latin_1")

        if metainfo.has_key("title"):
            print "Updating title to", metainfo["title"]
            file.tag.setTitle(enc(metainfo["title"])[0])
        if metainfo.has_key("album"):
            print "Updating album"
            file.tag.setAlbum(enc(metainfo["album"])[0])
        if metainfo.has_key("artist"):
            print "Updating artist"
            file.tag.setArtist(enc(metainfo["artist"])[0])
        if metainfo.has_key("year"):
            print "Updating year"
            file.tag.setDate(enc(metainfo["year"])[0])
        if metainfo.has_key("tracknr"):
            print "Updating tracknr", metainfo["tracknr"]
            if type(metainfo["tracknr"]) in types.StringTypes:
                metainfo["tracknr"] = (metainfo["tracknr"], None)
            file.tag.setTrackNum(metainfo["tracknr"])
        if metainfo.has_key("genre"):
            for genre in metainfo["genre"]:
                file.tag.setGenre(genre)
        if metainfo.has_key("artist_sortname"):
            file.tag.setTextFrame("TSOP", enc(metainfo["artist_sortname"])[0])
        if metainfo.has_key("mb_track_id"):
            self.setUFID(file.tag.frames, self.MB_OWNER_ID, metainfo["mb_track_id"])
        if metainfo.has_key("mb_artist_id"):
            self.setUserTextFrame(file.tag.frames, "TXXX", enc(self.MB_ARTIST_ID)[0],
                                  enc(metainfo["mb_artist_id"])[0])
        if metainfo.has_key("mb_album_id"):
            self.setUserTextFrame(file.tag.frames, "TXXX", enc(self.MB_ALBUM_ID)[0],
                                  enc(metainfo["mb_album_id"])[0])
        if metainfo.has_key("mb_trm_id"):
            self.setUserTextFrame(file.tag.frames, "TXXX", enc(self.MB_TRM_ID)[0],
                                  enc(metainfo["mb_trm_id"])[0])

        file.tag.update(mmpython.audio.eyeD3.ID3_V2_4)




# ------------------------------------------------------------
# OGG
# ------------------------------------------------------------


class OggMusicFile(MusicFile):
    
    ogg2key_mapping = {
        'ARTIST':                   'artist',
        'ALBUM':                    'album',
        'TITLE':                    'title',
        'DATE':                     'year',
        'TRACKNUMBER':              'tracknr',
        'GENRE':                    'genre',
        'MUSICBRAINZ_TRACKID':      'mb_track_id',
        'MUSICBRAINZ_TRMID':        'mb_trm_id',
        'MUSICBRAINZ_ARTISTID':     'mb_artist_id',
        'MUSICBRAINZ_ALBUMARTISTID':'mb_albumartist_id',
        'MUSICBRAINZ_ALBUMID':      'mb_album_id',
        'MUSICBRAINZ_SORTNAME':     'artist_sortname',
        }

    key2ogg_mapping = {}
    for key, value in ogg2key_mapping.items():
        key2ogg_mapping[value] = key

    singletons = [
        'ALBUM',
        'ARTIST',
        'TITLE',
        'TRACKNUMBER',
        'MUSICBRAINZ_TRACKID',
        'MUSICBRAINZ_TRMID',
        'MUSICBRAINZ_ARTISTID',
        'MUSICBRAINZ_ALBUMARTISTID',
        'MUSICBRAINZ_ALBUMID',
        'MUSICBRAINZ_SORTNAME',
        ]

    def __init__(self, filename):
        MusicFile.__init__(self, filename)
        import ogg.vorbis
        self.vf = ogg.vorbis.VorbisFile(self.filename)

    def get_trm(self):
        return get_trm(self.vf)

    def read(self, metainfo):
        vi = self.vf.info()
        vc = self.vf.comment()

        for key, value in vc.items():
            if self.ogg2key_mapping.has_key(key):
                metainfo[self.ogg2key_mapping[key]] = value
            else:
                logger.info("ogg: mapping lacking for %s", key)

        length = self.vf.time_total(0)
        metainfo["length"] = "00:%02d:%02d" % (length / 60, length % 60)

        metainfo["bitrate"] = self.vf.bitrate(0) / 1000.0
        metainfo["sample_freq"] = vi.rate
        metainfo["subtype"] = "vorbis version %d" % vi.version
        metainfo["audio_mode"] = vi.channels and "stereo" or "mono"


    def update(self, metainfo):
        vi = self.vf.info()
        vc = self.vf.comment()

        for key, value in metainfo.items():
            if self.key2ogg_mapping.has_key(key):
                tag = self.key2ogg_mapping[key]
                if tag in self.singletons:
                    vc[tag] = [value]
                elif value not in vc[tag]:
                    vc.add_tag(tag, value)

        vc.write_to(self.filename)



# ------------------------------------------------------------
# SID
# ------------------------------------------------------------


import types
import struct

class SIDtune(MusicFile):

    def __init__(self, filename):
        MusicFile.__init__(self, filename)

    def read(self, metainfo):
        file = file(self.filename, "rb")
        header = file.read(4)
        assert header in ("PSID", "RSID")

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
         self.copyright) = struct.unpack(sidformat,
                                         file.read(struct.calcsize(sidformat)))
        self.name = self.name.replace("\0", "")
        self.author = self.name.replace("\0", "")
        self.copyright = self.name.replace("\0", "")

        metainfo["subtype"] = "SID %d" % self.version
        return metainfo


mime_map = {
    'audio/mpeg':        MP3MusicFile,
    'application/ogg':   OggMusicFile,
    'audio/x-ogg':       OggMusicFile,
    'audio/prs.sid':     SIDtune,
    }
