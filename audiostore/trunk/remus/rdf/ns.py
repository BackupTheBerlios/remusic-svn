"""XML namespace management routines.

Keeping track of XML namespaces, and their prefizes.
"""

import types

# Redland RDF module
import RDF


__all__ = (
    'add_namespace',
    'namespaces',
    'namespace',
    'ns_prefix',
    'qname',
    'register_namespace',
    'uri2prefix_elem',
    'query_prefixes',
    )

namespaces = {}
uri2prefix = {}
ns_genid = 0


def namespace(prefix):
    """Returns the namespace URI for the given prefix.
    
    >>> print namespace('rdf').prefix
    http://www.w3.org/1999/02/22-rdf-syntax-ns#
    """
    return namespaces[prefix]


def add_namespace(prefix, uri):
    """Add a new namespace prefix definition.
        
    Maps 'prefix' to 'uri'

    >>> ex = add_namespace('ex', 'http://example.org/')
    >>> print ex.prefix
    http://example.org/
    >>> print namespaces['ex'].prefix
    http://example.org/
    >>> print ns_prefix('http://example.org/')
    ex
    """
    if type(uri) in types.StringTypes:
        uri = RDF.NS(uri)

    assert(namespaces.get(prefix, uri).prefix == uri.prefix)
    namespaces[prefix] = uri
    uri2prefix[uri.prefix] = prefix
    return uri


def register_namespace(uri):
    """Registers a new uri, generating a unique prefix.
        
    >>> print register_namespace('http://example2.org')
    _ns0

    Already registered namespaces return the previously allocated
    prefix.

    >>> print register_namespace('http://purl.org/dc/elements/1.1/')
    dc
    """
    if type(uri) in types.StringTypes:
        uri = RDF.NS(uri)
    
    if not uri2prefix.has_key(uri.prefix):
        global ns_genid #IGNORE:W0121
        prefix = "_ns%s" % ns_genid
        add_namespace(prefix, uri)
        ns_genid += 1
    else:
        prefix = uri2prefix[uri.prefix]
    return prefix


def ns_prefix(uri):
    """Returns the assigned prefix of the given URI.

    If the URI isn't assigned a prefix, an exception is returned
    (KeyError).

    >>> print ns_prefix('http://purl.org/dc/elements/1.1/')
    dc
    """
    if type(uri) not in types.StringTypes:
        uri = uri.prefix
    
    return uri2prefix[uri]


def uri2prefix_elem(uri):
    """Translates an URI to ('<namespace>', '<element>') tuple.
    
    >>> ex = add_namespace('ex', 'http://example.org/')
    >>> print uri2prefix_elem('http://example.org/title')
    ('ex', 'title')
    """
    end_of_common_uri = 0

    if type(uri) not in types.StringTypes:
        uri = str(uri.uri)

    # Check if there's an already registered uri which matches
    for prefix, existing_uri in namespaces.items():
        exuri = existing_uri.prefix
        if uri.startswith(exuri):
            end_of_common_uri = len(exuri)
            break

    if end_of_common_uri == 0:
        if uri.find("#") != -1:
            end_of_common_uri = uri.find("#")
        else:
            end_of_common_uri = uri.rfind("/")
        prefix = register_namespace(uri[:end_of_common_uri])

    return prefix, uri[end_of_common_uri:]


def qname(uri):
    """Make a 'qname' from an uri.

    A qname (qualified name) is a name in the form <ns>:<name>, where
    <ns> is the namespace prefix assigned to a prefix of 'uri'.

    >>> print qname('http://www.w3.org/1999/02/22-rdf-syntax-ns#Resource')
    rdf:Resource
    """
    return "%s:%s" % uri2prefix_elem(uri)


def query_prefixes(prefixes = namespaces):
    prefix_str = "PREFIX %s: <%s>"
    return '\n'.join([ prefix_str % (k, v.prefix)
                       for k, v in prefixes.items() ])


# Common namespaces
rdf     = add_namespace("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
rdfs    = add_namespace("rdfs", "http://www.w3.org/2000/01/rdf-schema#")
owl     = add_namespace("owl", "http://www.w3.org/2002/07/owl#")
xsd     = add_namespace("xsd", "http://www.w3.org/2001/XMLSchema#")
dc      = add_namespace("dc", "http://purl.org/dc/elements/1.1/")
dcterms = add_namespace("dcterms", "http://purl.org/dc/terms/")


def testsuite():
    import doctest
    import ns

    return doctest.DocTestSuite(ns)


def _test():
    import unittest
    unittest.main(defaultTest="testsuite")


if __name__ == "__main__":
    _test()
