#!/bin/sh
#
# $Id$
#
# Set up the development environment after first checkout.
#
# This script should be run before starting to work on this module.
#

# Create necessary automake files, etc
${aclocal:-aclocal}
${automake:-automake} --add-missing
${autoconf:-autoconf}
intltoolize --automake
