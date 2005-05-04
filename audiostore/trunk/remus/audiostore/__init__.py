from remus.audiostore.audiostore import *
from remus.audiostore.as_collection import *
from remus import config

config.add_section("autotagger")

config_defaults = {
    'levenshtein-threshold' : "5",
    'use-musicbrainz': "True",
    }
