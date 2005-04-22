dnl sqlml configure script
dnl Copyright (C) 2004  Daniel Larsson
dnl
dnl This program is free software; you can redistribute it and/or modify
dnl it under the terms of the GNU General Public License as published by
dnl the Free Software Foundation; either version 2 of the License, or
dnl (at your option) any later version.
dnl
dnl This program is distributed in the hope that it will be useful,
dnl but WITHOUT ANY WARRANTY; without even the implied warranty of
dnl MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
dnl GNU General Public License for more details.
dnl
dnl You should have received a copy of the GNU General Public License
dnl along with this program; if not, write to the Free Software
dnl Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


dnl Process this file with autoconf to produce a configure script.
 
AC_INIT(sqlml, 0.3.1)
AM_INIT_AUTOMAKE

RELEASE_DATE=2004-02-11
AC_SUBST(RELEASE_DATE)


dnl ==========================================================================

dnl Checks for programs.
AC_PROG_LN_S

dnl
dnl Check for xsltproc
dnl
AC_PATH_PROG(XSLTPROC, xsltproc)
if test -z "$XSLTPROC"; then
  AC_MSG_ERROR([xsltproc not found])
fi

dnl
dnl Check for dot
dnl
AC_PATH_PROG(DOT, dot)
AM_CONDITIONAL(HAVE_DOT, test -n "$DOT")


AC_OUTPUT(
Makefile
sqlml.make
setup.py
)
