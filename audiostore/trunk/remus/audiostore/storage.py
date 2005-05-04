"""Storage for the remus database.

The storage is an RDF store.
"""

import types
import RDF
import remus.rdf.ns

from remus.rdf.ns import rdf, rdfs, dc, xsd

# Musicbrainz namespaces
mm   = remus.rdf.ns.add_namespace("mm", "http://musicbrainz.org/mm/mm-2.1#")
mq   = remus.rdf.ns.add_namespace("mq", "http://musicbrainz.org/mm/mq-1.1#")
ar   = remus.rdf.ns.add_namespace("ar", "http://musicbrainz.org/ar/ar-1.0#")

# Remus namespaces
rem  = remus.rdf.ns.add_namespace(
    "remus", "http://remusic.berlios.de/remus/1.0#")
remtrack = remus.rdf.ns.add_namespace(
    "remtrack", "http://remusic.berlios.de/remustrack/")


_SPARQL_QUERY = """%s
SELECT %%(_distinct)s %%(fieldlist)s
WHERE  %%(selection)s
""" % remus.rdf.ns.query_prefixes()


def sparql_query(fields, select, distinct=False):
    if fields in types.StringTypes:
        fieldlist = "?" + fields
    else:
        fieldlist = ', '.join(["?" + field for field in fields])

    _distinct = ("", "DISTINCT")[distinct]
    
    selection = "\n".join(["(%s)" % (' '.join(stmnt)) for stmnt in select])
    print _SPARQL_QUERY % locals()
    return RDF.SPARQLQuery(_SPARQL_QUERY % locals())


class MysqlStorage(RDF.Storage):
    def __init__(self, host="localhost", database="remus",
                 user="remus", password=""):
        RDF.Storage(self, storage_name="mysql",
                    options_string="host=%(host)s,database=%(database)s,"
                    "user=%(user)s, password=%(password)s" % locals())


class HashStorage(RDF.HashStorage):
    def __init__(self, options=None):
        opts = "hash-type='bdb'"
        if options:
            opts += "," + options
        RDF.HashStorage.__init__(self, "/var/db/audiostore/remus",
                                 options=opts)


class RemusStore(RDF.Model):

    def __init__(self, storage=None):
        try:
            storage = storage or HashStorage()
        except RDF.RedlandError:
            storage = HashStorage("new='true'")
        RDF.Model.__init__(self, storage)

    def genres(self):
        import sets
        genres = sets.Set()
        for genre in self.find_statements(
            RDF.Statement(None, rem.genre, None)):
            genres.add(genre.object.literal_value['string'])
        return genres
        
    def albums(self):
        return self.get_sources(rdf.type, mm.Album)

    def artists(self):
        return self.get_sources(rdf.type, mm.Artist)

    def tracks(self):
        return self.get_sources(rdf.type, mm.Track)

