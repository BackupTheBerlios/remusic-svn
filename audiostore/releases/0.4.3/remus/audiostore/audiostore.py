"""Interface to the audiostore database.

This module contains functions to manipulate the audiostore, such as adding
audio clips, change their meta information, etc.
"""

import os
import copy
import logging
import stat

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

try:
    import musicbrainz
    from musicbrainz.queries import *
    HAVE_MUSICBRAINZ = True
except ImportError:
    HAVE_MUSICBRAINZ = False
    pass

from sqlquery import *
import as_collection

from db_audiostore import *

logger = logging.getLogger("remus.audiostore.mysql")

__all__ = (
    "Interface",
    "AudioObject",
    )

class Interface:
    """Interface to the audiostore database.

    This interface enables adding songs to the database, and do various
    types administrative tasks, such as updating the database from the
    audio files (e.g. if file tags have changed), or update database
    and file tags on collection of files (e.g. rename an album).
    """

    default_fields = {
        'artist':      'Unknown',
        'artist_sort': 'Unknown',
        'artist_id':   None,
        'album':       'Unknown',
        'album_id':    None,
        'title':       'Unknown',
        'composer':    'Unknown',
        'year':        None,
        'length':      None,
        'tracknr':     None,
        'bitrate':     None,
        'sample_freq': None,
        'bitrate':     None,
        'audio_mode':  None,
        'subtype':     None,
        'genre':       None,
        }
    
    def __init__(self, database):
        self.db = database

    def root(self):
        return as_collection.RootColl(self)

    def add(self, mimetype, filename):
        """Add audio clip of type 'mimetype' to the database."""
        logger.info("Trying to add %s [%s]", filename, mimetype)
        try:
            metafields = copy.deepcopy(self.default_fields)
            metafields["mimetype"] = mimetype
            metafields["filename"] = filename
        
            mime_map[mimetype].read(filename, metafields)

            try:
                cursor = self.db.cursor()

                select = Select()
                select.addcolumn(remus_audio_objects.au_id)
                query = AND(
                    EQUAL(remus_artists.art_name,
                          self.db.literal(metafields['artist'])),
                    EQUAL(remus_albums.alb_name,
                          self.db.literal(metafields['album'])),
                    EQUAL(remus_audio_objects.au_title,
                          self.db.literal(metafields['title'])))
                
                count = cursor.execute(select.select(query=query))
                
                if count == 0:
                    metafields["art_id"] = self.add_artist(metafields)
                    metafields["alb_id"] = self.add_album(metafields)
                    metafields["ge_id"] = self.add_genre(metafields)
                    cursor.execute(
                        """INSERT INTO remus_audio_objects
                        VALUES (
                          NULL,
                          %(title)s,
                          %(art_id)s,
                          %(alb_id)s,
                          %(ge_id)s,
                          %(mimetype)s,
                          %(year)s,
                          %(length)s,
                          %(tracknr)s,
                          NOW(),
                          NOW(),
                          %(bitrate)s,
                          %(sample_freq)s,
                          %(audio_mode)s,
                          %(subtype)s,
                          %(filename)s)
                          """, metafields)
                else:
                    print metafields
                    raise IOError("File already present")

                cursor.close()
                self.db.commit()
            except KeyError:
                logger.exception("Failed to store clip in database")
                self.db.rollback()
                raise IOError("Failed to store in database")

        except KeyError:
            logger.exception("Error!")
            raise IOError("Unsupported format")

    def add_artist(self, metafields):
        cursor = self.db.cursor()

        if metafields["artist_sort"] == "Unknown":
            a = metafields["artist"]
            if a[:4].lower() == "the ":
                a = a[4:] + ", " + a[:3]
            metafields["artist_sort"] = a


        if metafields["artist_id"]:
            match = "art_mb_artist_id=%(artist_id)s"
        else:
            match = "art_name=%(artist)s"
        count = cursor.execute(
            """SELECT
                   art_id
               FROM
                   remus_artists
               WHERE
            """ + match, metafields)

        if count == 0:
            cursor.execute(
                """INSERT INTO remus_artists
                   VALUES (
                     NULL,
                     %(artist)s,
                     %(artist_sort)s,
                     %(artist_id)s,
                     NULL,
                     NOW(),
                     NOW())
                """, metafields)
            return cursor.lastrowid
        else:
            return cursor.fetchone()[0]

    def add_album(self, metafields):
        cursor = self.db.cursor()

        if metafields["album_id"]:
            match = "alb_mb_album_id=%(album_id)s"
            album_id = metafields["album_id"]
        else:
            match = "alb_name=%(album)s"
            album_id = "NULL"
        count = cursor.execute(
            """SELECT
                   alb_id
               FROM
                   remus_albums
               WHERE
            """ + match, metafields)

        if count == 0:
            cursor.execute(
                """INSERT INTO remus_albums
                   VALUES (
                     NULL,
                     %(album)s,
                     %(album_id)s,
                     NULL,
                     NULL,
                     NOW(),
                     NOW(),
                     NULL)
                """, metafields)
            return cursor.lastrowid
        else:
            return cursor.fetchone()[0]

    def add_genre(self, metafields):
        cursor = self.db.cursor()

        if not metafields["genre"]:
            metafields["genre"] = "unknown"

        count = cursor.execute(
            """SELECT
                   ge_id
               FROM
                   remus_genres
               WHERE
                   ge_genre=%(genre)s
            """, metafields)

        if count == 0:
            cursor.execute(
                """INSERT INTO remus_genres
                   VALUES (
                     NULL,
                     %(genre)s)
                """, metafields)
            return cursor.lastrowid
        else:
            return cursor.fetchone()[0]


    def resync(self, query=None):
        cursor = self.db.cursor()

        select = Select()
        select.addcolumn(remus_audio_objects.au_id)
        select.addcolumn(remus_audio_objects.au_audio_clip)
        select.addcolumn(remus_audio_objects.au_content_type)
        sql = select.select(query=query)

        count = cursor.execute(sql)

        logger.info("Resyncing %d audio clips", count)
    
        self.resync_from_cursor(cursor)


    def resync_from_cursor(self, cursor):
        """Update database with information from file tag.

        Internal routine.
        
        'cursor' must be a database cursor which executed a query
        returning the fields 'au_id', 'au_audio_clip' and 'au_content_type'
        (in this order).
        """
        for au_id, filename, mimetype in cursor:
            metafields = copy.deepcopy(AudiostoreInterface.default_fields)
            metafields["id"] = au_id
            metafields["mimetype"] = mimetype
            metafields["filename"] = filename
            mime_map[mimetype].read(filename, metafields)

            metafields["art_id"] = self.add_artist(metafields)
            metafields["alb_id"] = self.add_album(metafields)
            metafields["ge_id"] = self.add_genre(metafields)
            update_cur = cursor.connection.cursor()
            sql = """
                UPDATE
                    remus_audio_objects
                SET
                    au_title=%(title)s,
                    au_artist=%(artist_id)s,
                    au_album=%(album_id)s,
                    au_genre=%(ge_id)s,
                    au_content_type=%(mimetype)s,
                    au_length=%(length)s,
                    au_track_number=%(tracknr)s,
                    au_year=%(year)s,
                    au_bitrate=%(bitrate)s,
                    au_sample_freq=%(sample_freq)s,
                    au_audio_mode=%(audio_mode)s,
                    au_subtype=%(subtype)s,
                    au_modified=NOW()
                WHERE
                    au_id=%(id)s
                """

            try:
                update_cur.execute(sql, metafields)
            except:
                import sys
                logger.error("Failed updating %(title)s (filename %(filename)s)" %
                             metafields)
                logger.info("Traceback", exc_info=1)
                logger.info("SQL statement was: %s",
                            sql % cursor.connection.literal(metafields))

            logger.info("Updated %(title)s" % metafields)


class AudioObject:
    def __init__(self, store, auid):
        self.store = store
        self.auid = auid

    def init_from_db(self):
        from MySQLdb.cursors import DictCursor
        cursor = self.store.db.cursor(DictCursor)
        cursor.execute(
            """SELECT *
               FROM
                   remus_audio_objects,
                   remus_artists,
                   remus_albums,
                   remus_genres
               WHERE
                   au_artist = art_id AND
                   au_album = alb_id AND
                   au_genre = ge_id AND
                   au_id = %s""" % self.auid)
        result = cursor.fetchone()
        for key, value in result.items():
            setattr(self, key, value)
        
    def resync_from_file(self):
        cursor = self.store.db.cursor()
        count = cursor.execute("""
            SELECT
                au_id, au_audio_clip, au_content_type
            FROM
                remus_audio_objects
            WHERE
                au_id = %s""", self.auid)

        self.store.resync_from_cursor(cursor)

    def remove(self):
        cursor = self.store.db.cursor()

        cursor.execute("""
            SELECT
                au_audio_clip
            FROM
                remus_audio_objects
            WHERE
                au_id=%s""", self.auid)

        rows = cursor.fetchone()

        if rows:
            filename = rows[0]
    
            cursor.execute("DELETE FROM remus_audio_objects WHERE au_id=%s",
                           self.auid)
            try:
                os.unlink(filename)
            except OSError:
                pass
            return True
        else:
            return False

    if HAVE_MUSICBRAINZ:

        class Track:
            pass

        class Album:
            pass

        def get_trm(self):
            self.init_from_db()
            trm = mime_map[self.au_content_type].get_trm(self.au_audio_clip)

            mb = musicbrainz.mb()
            mb.SetDepth(6)

            mb.QueryWithArgs(MBQ_GetTrackByTRMId, [trm])

            # Check to see how many items were returned from the server
            numTracks = mb.GetResultInt(MBE_GetNumTracks)

            tracks = []
            
            for ii in range(1, numTracks+1):

                track = self.Track()
                
                # Start at the top of the query and work our way down
                mb.Select(MBS_Rewind)  

                # Select the ith artist
                mb.Select1(MBS_SelectTrack, ii)  

                # Extract the artist name from the ith track
                track.artist = mb.GetResultData(MBE_TrackGetArtistName)

                # Extract the track name from the ith track
                track.title = mb.GetResultData(MBE_TrackGetTrackName)

                # Extract the track name from the ith track
                track.duration = mb.GetResultInt(MBE_TrackGetTrackDuration)

                # Extract the artist id from the ith track
                temp = mb.GetResultData(MBE_TrackGetArtistId)
                track.artist_id = mb.GetIDFromURL(temp)

                tracks.append(track)

                track.albums = []
                
                # Extract the number of albums 
                numAlbums = mb.GetResultInt(MBE_GetNumAlbums)

                for jj in range(1, numAlbums+1):
                    album = self.Album()

                    # Select the jth album in the album list
                    mb.Select1(MBS_SelectAlbum, jj)  

                    # Extract the album name 
                    album.name = mb.GetResultData(MBE_AlbumGetAlbumName),
            
                    temp = mb.GetResultData(MBE_AlbumGetAlbumId)
                    album.id = mb.GetIDFromURL(temp),
        
                    # How many tracks on this cd
                    album.nr_of_tracks = mb.GetResultInt(MBE_AlbumGetNumTracks)
            
                    # Back up one level and go back to the artist level 
                    mb.Select(MBS_Back)  

                    track.albums.append(album)

            return tracks

# ------------------------------------------------------------
# Extract meta information from files
# ------------------------------------------------------------

def get_trm(ff):
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


class MetaInfo_mp3:

    def get_trm(self, filename):
        ff = MadWrapper(filename)
        return get_trm(ff)

    def read(self, filename, metainfo):
        import mmpython
        try:
            minfo = mmpython.parse(filename)
        except TypeError:
            logger.exception("MP3 tag parse error")

        try:
            if minfo.title:
                metainfo["title"] = minfo.title
            if minfo.genre:
                metainfo["genre"] = minfo.genre
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

        import mmpython.audio.eyeD3
        file = mmpython.audio.eyeD3.Mp3AudioFile(filename)
        metainfo["bitrate"] = file.getBitRateString()
        metainfo["samplefreq"] = file.header.sampleFreq
        metainfo["audio_mode"] = file.header.mode
        metainfo["subtype"] = "MPEG %s layer %s" % (file.header.version,
                                                    'I' * file.header.layer)
        logger.info(str(metainfo))


    def update(self, filename, metainfo):
        import mmpython.audio.eyeD3
        file = mmpython.audio.eyeD3.Mp3AudioFile(filename)

        if metainfo.has_key("title"):
            file.tag.setTitle(metainfo["title"])
        if metainfo.has_key("album"):
            file.tag.setAlbum(metainfo["album"])
        if metainfo.has_key("artist"):
            file.tag.setArtist(metainfo["artist"])
        if metainfo.has_key("year"):
            file.tag.setDate(metainfo["year"])
        if metainfo.has_key("tracknr"):
            file.tag.setTrackNum(metainfo["tracknr"])
        if metainfo.has_key("genre"):
            file.tag.setGenre("genre")

        # Saving as 2.3 instead of 2.4, since id3v2 doesn't seem to
        # recognize 2.4 yet.
        file.tag.update(mmpython.audio.eyeD3.ID3_V2_3)


metainfo_mp3 = MetaInfo_mp3()

# ------------------------------------------------------------
# OGG
# ------------------------------------------------------------



class MetaInfo_ogg:
    
    ogg_mapping = {
        'ARTIST':     'artist',
        'ALBUM':      'album',
        'TITLE':      'title',
        'DATE':       'year',
        'TRACKNUMBER':'tracknr',
        'GENRE':      'genre',
        }

    def generate_trm(self, filename):
        import ogg.vorbis
        ff = ogg.vorbis.VorbisFile(filename)
        return get_trm(ff)

    def read(self, filename, metainfo):
        import ogg.vorbis

        vf = ogg.vorbis.VorbisFile(filename)
        vi = vf.info()
        vc = vf.comment()

        for key, value in vc.items():
            metainfo[ogg_mapping[key]] = value

        length = vf.time_total(0)
        metainfo["length"] = "00:%02d:%02d" % (length / 60, length % 60)

        metainfo["bitrate"] = vf.bitrate(0) / 1000.0
        metainfo["sample_freq"] = vi.rate
        metainfo["subtype"] = "vorbis version %d" % vi.version
        metainfo["audio_mode"] = vi.channels and "stereo" or "mono"


    def update(self, filename, metainfo):
        import ogg.vorbis
        
        vf = ogg.vorbis.VorbisFile(filename)
        vi = vf.info()
        vc = vf.comment()

        if metainfo.has_key("title"):
            vc["TITLE"] = [metainfo["title"]]
        if metainfo.has_key("album"):
            vc["ALBUM"] = [metainfo["album"]]
        if metainfo.has_key("artist"):
            vc["ARTIST"] = [metainfo["artist"]]
        if metainfo.has_key("year"):
            vc["DATE"] = [metainfo["year"]]
        if metainfo.has_key("tracknr"):
            vc["TRACKNUMBER"] = [metainfo["tracknr"]]
        if metainfo.has_key("genre"):
            vc["GENRE"] = [metainfo["genre"]]

        vc.write_to(filename)


metainfo_ogg = MetaInfo_ogg()


# ------------------------------------------------------------
# SID
# ------------------------------------------------------------


class MetaInfo_sid:

    def read(self, filename, metainfo):
        
        try:
            if minfo.title:
                metainfo["title"] = minfo.title
            if minfo.genre:
                metainfo["genre"] = minfo.genre
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

        import mmpython.audio.eyeD3
        file = mmpython.audio.eyeD3.Mp3AudioFile(filename)
        metainfo["bitrate"] = file.getBitRateString()
        metainfo["samplefreq"] = file.header.sampleFreq
        metainfo["audio_mode"] = file.header.mode
        metainfo["subtype"] = "MPEG %s layer %s" % (file.header.version,
                                                    'I' * file.header.layer)


    def update(self, filename, metainfo):
        import mmpython.audio.eyeD3
        file = mmpython.audio.eyeD3.Mp3AudioFile(filename)

        if metainfo.has_key("title"):
            file.tag.setTitle(metainfo["title"])
        if metainfo.has_key("album"):
            file.tag.setAlbum(metainfo["album"])
        if metainfo.has_key("artist"):
            file.tag.setArtist(metainfo["artist"])
        if metainfo.has_key("year"):
            file.tag.setDate(metainfo["year"])
        if metainfo.has_key("tracknr"):
            file.tag.setTrackNum(metainfo["tracknr"])
        if metainfo.has_key("genre"):
            file.tag.setGenre("genre")

        # Saving as 2.3 instead of 2.4, since id3v2 doesn't seem to
        # recognize 2.4 yet.
        file.tag.update(mmpython.audio.eyeD3.ID3_V2_3)


metainfo_sid = MetaInfo_sid()




mime_map = {
    'audio/mpeg':        metainfo_mp3,
    'application/ogg':   metainfo_ogg,
    'audio/x-ogg':       metainfo_ogg,
    'audio/prs.sid':     metainfo_sid,
    }
