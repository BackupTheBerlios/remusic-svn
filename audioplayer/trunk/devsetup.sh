#!/bin/sh
#
# $Id$
#
# Set up the development environment after first checkout.
#
# To be able to build documentation, and other items, various common
# files are needed. These are part of the 'projecttools' module, and
# we're checking out those parts at appropriate places here.
#
# This script should be run before starting to work on this module.
#

# Figure out where our repository is
URL_BASE=$(svn info | grep URL | sed -e 's/URL: //' -e 's%remus/.*%remus%')

# Branch from projecttools to use
PROJTOOLS_BRANCH=${PROJTOOLS_BRANCH:-trunk}

PROJTOOLS_URL=$URL_BASE/projecttools/$PROJTOOLS_BRANCH

# Check out parts of projecttools at appropriate places
$doit svn checkout $PROJTOOLS_URL/doc/xsl doc/xsl
$doit svn checkout $PROJTOOLS_URL/doc/xml doc/xml
$doit svn checkout $PROJTOOLS_URL/doc/mk  doc/mk

# Create necessary automake files, etc
${aclocal:-aclocal}
${automake:-automake} --add-missing
${autoconf:-autoconf}
