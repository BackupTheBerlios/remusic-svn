"""Classes to build audiostore queries.

It's possible to perform operations on subsets of the audio store, and
these query classes are used to define such subsets.

Example:

  # Change all artist names like "The Hives", "Hives", "Hives, the", etc
  # to "Hives"
  >>> query = LIKE(ARTIST, '%Hives%')
  >>> coll = AudiostoreCollection(store, query)
  >>> coll["artist"] = "Hives"
  >>> coll.update()

  # Remove all songs by 22 Pistepirkko from the Big Lupu album
  >>> query = AND(EQUAL(ARTIST, "22 Pistepirkko"), EQUAL(ALBUM, "Big Lupu"))
  >>> coll = AudiostoreCollection(store, query)
  >>> coll.remove()
"""


__all__ = (
    "AND",
    "OR",
    "LIKE",
    "REGEXP",
    "EQUAL",
    "ALBUM",
    "ARTIST",
    "TITLE",
    "ALBUM_EQ",
    "ALBUM_LIKE",
    "ARTIST_EQ",
    "ARTIST_LIKE",
    "TITLE_EQ",
    "TITLE_LIKE",
    "Field",
    )


class AudiostoreQueryBinaryOp:
    def __init__(self, left, right):
        assert left and right
        self.left = left
        self.right = right

    def expr(self):
        import types

        if type(self.left) in types.StringTypes:
            left = self.left
            left_arg = ()
        else:
            left, left_arg = self.left.expr()
            
        if type(self.right) in types.StringTypes:
            right = "%s"
            right_arg = (self.right,)
        else:
            right, right_arg = self.right.expr()

        if type(left_arg) != types.TupleType:
            left_arg = (left_arg,)
        if type(right_arg) != types.TupleType:
            right_arg = (right_arg,)

        return "(%s %s %s)" % (left, self.OP, right), left_arg + right_arg


class AudiostoreQueryAND(AudiostoreQueryBinaryOp):
    OP = "AND"

class AudiostoreQueryOR(AudiostoreQueryBinaryOp):
    OP = "OR"

class AudiostoreQueryLIKE(AudiostoreQueryBinaryOp):
    OP = "LIKE"

class AudiostoreQueryREGEXP(AudiostoreQueryBinaryOp):
    OP = "REGEXP"

class AudiostoreQueryEqual(AudiostoreQueryBinaryOp):
    OP = "="


def AND(left, right):
    return AudiostoreQueryAND(left, right)

def OR(left, right):
    return AudiostoreQueryOR(left, right)

def LIKE(left, right):
    return AudiostoreQueryLIKE(left, right)

def REGEXP(left, right):
    return AudiostoreQueryREGEXP(left, right)

def EQUAL(left, right):
    return AudiostoreQueryEqual(left, right)


# ------------------------------------------------------------
#  Field constants
# ------------------------------------------------------------

class Field:
    def __init__(self, field):
        self.field = field
    def expr(self):
        return self.field, ()
    
ALBUM  = Field("au_album")
ARTIST = Field("au_artist")
TITLE  = Field("au_title")


# Convenience functions

def ALBUM_EQ(text):
    return EQUAL(ALBUM, text)

def ALBUM_LIKE(text):
    return LIKE(ALBUM, text)

def ARTIST_EQ(text):
    return EQUAL(ARTIST, text)

def ARTIST_LIKE(text):
    return LIKE(ARTIST, text)

def TITLE_EQ(text):
    return EQUAL(TITLE, text)

def TITLE_LIKE(text):
    return LIKE(TITLE, text)
