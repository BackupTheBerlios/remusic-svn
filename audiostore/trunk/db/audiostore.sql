--
-- Create database and tables
--

CREATE DATABASE IF NOT EXISTS remus;

USE remus;


--
-- Artist table
--

CREATE TABLE IF NOT EXISTS remus_artists (
        -- table key
        art_id                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
        -- artist name
        art_name                VARCHAR(60),
        -- artist sort name
        art_sort_name           VARCHAR(60),
        -- musicbrainz artist id (UUID)
        art_mb_artist_id        CHAR(36),
        -- optional artist URL
        art_url                 VARCHAR(128),
        -- last modified
        art_modified            TIMESTAMP,
        -- creation date
        art_created             TIMESTAMP,

        PRIMARY KEY (art_id),
        INDEX       (art_id)
) TYPE = InnoDB;


--
-- Album table
--

CREATE TABLE IF NOT EXISTS remus_albums (
        -- table key
        alb_id                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
        -- album name
        alb_name                VARCHAR(60),
        -- key to artist table
        alb_artist              INT UNSIGNED,
        -- musicbrainz album id (UUID)
        alb_mb_album_id         CHAR(36),
        -- nr of tracks
        alb_nr_of_tracks        INT UNSIGNED,
        -- album length
        alb_duration            TIME,
        -- last modified
        alb_modified            TIMESTAMP,
        -- creation date
        alb_created             TIMESTAMP,

        PRIMARY KEY (alb_id),
        INDEX       (alb_id),
        INDEX       (alb_artist),
        FOREIGN KEY (alb_artist) REFERENCES remus_artists(art_id)
                ON DELETE RESTRICT
) TYPE = InnoDB;


--
-- The table containing search keywords
--

CREATE TABLE IF NOT EXISTS remus_genre (
        ge_id                   SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
        ge_genre                VARCHAR(30) NOT NULL,
        PRIMARY KEY (ge_id)
) TYPE = InnoDB;


--
-- The table containing the audio objects
--

CREATE TABLE IF NOT EXISTS remus_audio_objects (
        -- table key
        au_id                   INT UNSIGNED NOT NULL AUTO_INCREMENT,
        -- key to artist table
        au_artist               INT UNSIGNED,
        -- key to album table
        au_album                INT UNSIGNED,
        -- key to genre table
        au_genre                INT UNSIGNED NOT NULL,
        -- song title
        au_title                VARCHAR(60),
        -- mime type
        au_content_type         VARCHAR(40),
        -- year 
        au_year                 YEAR,
        -- song length
        au_length               TIME,
        -- track number in album
        au_track_number         SMALLINT UNSIGNED,
        -- last modified
        au_modified             TIMESTAMP,
        -- creation date
        au_created              TIMESTAMP,
        -- bitrate (kbps)
        au_bitrate              INT UNSIGNED,
        -- sample frequency (Hz)
        au_sample_freq          INT UNSIGNED,
	-- stereo / mono
        au_audio_mode           VARCHAR(20),
        -- subtype of clip (informational string just for presentation,
        -- e.g. "MPEG 1 layer III")
        au_subtype              VARCHAR(40),
        -- filename where actual audio clip is stored
        au_audio_clip           VARCHAR(128) NOT NULL,

        PRIMARY KEY (au_id),
        INDEX       (au_artist),
        FOREIGN KEY (au_artist) REFERENCES remus_artists(art_id)
                ON DELETE RESTRICT,
        INDEX       (au_album),
        FOREIGN KEY (au_album)  REFERENCES remus_albums(alb_id)
                ON DELETE RESTRICT,
        INDEX       (au_genre),
        FOREIGN KEY (au_genre)  REFERENCES remus_genre(ge_id)
                ON DELETE RESTRICT
) TYPE = InnoDB;


--
-- The playlist table
--

CREATE TABLE IF NOT EXISTS remus_playlists (
        -- table key
        pl_id                   INT UNSIGNED NOT NULL AUTO_INCREMENT,
	-- playlist name
	pl_name			VARCHAR(100),

	PRIMARY KEY(pl_id)
) TYPE = InnoDB;


--
-- Playlist contents table
--

CREATE TABLE IF NOT EXISTS remus_playlist_contents (
	-- what playlist I'm part of
	plcnt_pl		INT UNSIGNED,
	-- song in playlist
	plcnt_song		INT UNSIGNED,

        INDEX       (plcnt_pl),
        FOREIGN KEY (plcnt_pl) REFERENCES remus_playlists(pl_id)
                ON DELETE CASCADE,
        INDEX       (plcnt_song),
        FOREIGN KEY (au_artist) REFERENCES remus_audio_objects(au_id)
                ON DELETE CASCADE
) TYPE = InnoDB;
