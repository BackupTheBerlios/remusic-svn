# copyright (c) 2003 Daniel Larsson

dnl Process this file with autoconf to produce a configure script.
 
AC_INIT(remus-audiostore, 0.3.0)
AM_INIT_AUTOMAKE

RELEASE_DATE=2004-01-10
AC_SUBST(RELEASE_DATE)

dnl ==========================================================================
dnl
dnl If you add a version number here, you *must* add an AC_SUBST line for
dnl it too, or it will never make it into the spec file!
dnl
dnl ==========================================================================

SCROLLKEEPER_BUILD_REQUIRED=0.3.4
AC_SUBST(SCROLLKEEPER_BUILD_REQUIRED)

dnl ==========================================================================

dnl Checks for programs.
AC_PROG_LN_S

dnl
dnl Check for scrollkeeper
dnl
AC_PATH_PROG(SCROLLKEEPER_CONFIG, scrollkeeper-config,no)
if test x$SCROLLKEEPER_CONFIG = xno; then
  AC_MSG_ERROR(Couldn't find scrollkeeper-config. Please install the scrollkeeper package: http://scrollkeeper.sourceforge.net)
fi

dnl
dnl Check for docbook-xsl
dnl

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
setup.py
Makefile
db/Makefile
doc/Makefile
doc/xsl/Makefile
doc/xsl/fo/Makefile
doc/xml/project.ent
doc/manual/Makefile
doc/manual/C/Makefile
doc/manual/C/remus-audiostore-C.omf
)
