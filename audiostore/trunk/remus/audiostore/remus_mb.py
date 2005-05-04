"""Musicbrainz query routines.
"""

import codecs
import musicbrainz
import RDF

import remus
import remus.rdf.ns

from remus.audiostore import config_defaults
from remus.audiostore.storage \
     import rdf, dc, mm, mq, rem, remtrack


MAX_LEV_DIST = int(remus.config.get('autotagger', 'levenshtein-threshold',
                                    vars=config_defaults))

_RESULT_TRACK = """%s
SELECT ?track
WHERE (?result rdf:type mq:Result)
      (?result mm:trackList ?bag)
      (?bag rdf:_1 ?track)
""" % remus.rdf.ns.query_prefixes()

_RESULT_ARTIST = """%s
SELECT ?artist
WHERE (<%%s(track)s> dc:creator ?artist)
""" % remus.rdf.ns.query_prefixes()

_RESULT_ALBUM = """%s
SELECT ?album, ?albumname
WHERE (<%%s> mq:album ?album)
      (?album dc:title ?albumname)
""" % remus.rdf.ns.query_prefixes()

_RESULT_TRACKNR = """%s
SELECT ?tracknr
WHERE (<%%s> mq:album ?album)
      (?album mm:trackList ?seq)
      (?seq ?tracknr <%%s>)
""" % remus.rdf.ns.query_prefixes()



def get_info(trm, info):
    """Get metainfo from musicbrainz.

    Gets metainformation from musicbrainz about a song with the given
    acoustic fingerprint.

    Parameters:
      trm  - A musicbrainz acoustic id
      info - Dictionary with values from tag

    Returns:
      (matches, model) where 'matches' is the number of matches
      musicbrainz returned, and 'model' is a Redland RDF model of the
      returned data.
    """

    print "TRM is", str(trm)
    # Build query
    m = musicbrainz.mb()
    # TODO: Fill me in
    #m.SetServer("www.musicbrainz.org")
    m.SetDepth(2)
    m.SetDebug(10)

    artistname = info.get('artist', '__NULL__')
    albumname  = info.get('album', '__NULL__')
    trackname  = info.get('title', '__NULL__')
    tracknr    = info.get('tracknr', '__NULL__')
    duration   = "__NULL__"

    m.QueryWithArgs(musicbrainz.MBQ_TrackInfoFromTRMId,
                    [trm, artistname, albumname, trackname,
                     tracknr, duration])

    # Check to see how many items were returned from the server
    numTracks = m.GetResultInt(musicbrainz.MBE_GetNumTracks)

    matched_tracks = m.GetResultInt(musicbrainz.MBE_GetNumTracks)

    # Only update if we get a single match
    if matched_tracks == 1:

        querymodel = RDF.Model()
        rdf = m.GetResultRDF()
        parser = RDF.Parser(mime_type="application/rdf+xml")
        enc = codecs.getencoder("latin_1")
        parser.parse_string_into_model(
            querymodel, rdf, "http://example.com/" + enc(trm)[0])

    else:
        querymodel = None

    return matched_tracks, querymodel


def update(musicfile, info, querymodel, model):
    track_node = None

    for track in RDF.SPARQLQuery(_RESULT_TRACK).execute(querymodel):
        track_node = track['track']
        break

    assert track_node

    # Extract info from the RDF
    track_title = model.get_target(track_node, dc.title)
    if track_title:

        title = track_title.literal_value['string']

        # If we found a title in the tags, don't accept the
        # musicbrainz value if it differs too much
        dist = levenshtein_distance(title, info.get('title', title))

        if dist <= MAX_LEV_DIST:

            # Close enough
            if dist != 0:
                print "Changing title from", title, "to", info['title']
            info['title'] = track_title.literal_value['string']

        else:
            print "Rejecting musicbrainz data: Title differ too much"
            print "  From tag:        ", info['title']
            print "  From musicbrainz:", title
            return None
            
    info['mb_track_id'] = str(track_node.uri).split('/')[-1]

    # Update artist info
    artist = model.get_target(track_node, dc.creator)

    if artist:
        info['mb_artist_id'] = str(artist.uri).split('/')[-1]
        artist_sortname = model.get_target(artist, mm.sortName)

        if artist_sortname:
            info['artist_sortname'] = artist_sortname.literal_value['string']

        artistname = model.get_target(artist, dc.title)

        if artistname:
            info['artist'] = artistname.literal_value['string']

    for album in RDF.SPARQLQuery(_RESULT_ALBUM % track_node.uri).execute(model):
        info['album'] = album["albumname"].literal_value['string']
        info['mb_album_id'] = str(album['album'].uri).split('/')[-1]

    tnr = get_tracknr(track_node, model)
    if tnr:
        info['tracknr'] = tnr

    # If a model was given, insert the statements musicbrainz
    # gave us
    if model != None:
        merge_rdf(model, querymodel, track_node)

    return track_node


def merge_rdf(model, merge, node):
    """Add statements about 'track' in 'merge' to 'model'"""
    for stmnt in merge.find_statements(RDF.Statement(node, None, None)):
        model.append(stmnt)
        # Recursively add statements about objects which are
        # resources (e.g. artists and albums)
        if stmnt.object.is_resource() or stmnt.object.is_blank() and \
           model.find_statements(RDF.Statement(stmnt.object, None, None)).end():
            merge_rdf(model, merge, stmnt.object)


def get_tracknr(track, model):
    for result in RDF.SPARQLQuery(_RESULT_TRACKNR % (
        track.uri, track.uri)).execute(model):
        return int(str(result['tracknr'].uri).split("#_")[1]), None
    return None


def levenshtein_distance(a,b):
    "Calculates the Levenshtein distance between a and b."
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        a,b = b,a
        n,m = m,n

    current = range(n+1)
    for i in range(1,m+1):
        previous, current = current, [i]+[0]*m
        for j in range(1,n+1):
            add, delete = previous[j]+1, current[j-1]+1
            change = previous[j-1]
            if a[j-1] != b[i-1]:
                change = change + 1
            current[j] = min(add, delete, change)
            
    return current[n]


