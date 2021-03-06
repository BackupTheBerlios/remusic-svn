# copyright (c) 2003 Daniel Larsson

dnl Process this file with autoconf to produce a configure script.
 
AC_INIT(remus-audiostore, 0.4.3, daniel.j.larsson@chello.se)
AM_INIT_AUTOMAKE

RELEASE_DATE=2005-04-22
AC_SUBST(RELEASE_DATE)

# FreeBSD needs these
CPPFLAGS="$CPPFLAGS -I/usr/local/include"
LDFLAGS="$LDFLAGS -L/usr/local/lib"

AC_PROG_INTLTOOL
AM_MAINTAINER_MODE

dnl ==========================================================================
dnl
dnl If you add a version number here, you *must* add an AC_SUBST line for
dnl it too, or it will never make it into the spec file!
dnl
dnl ==========================================================================

SCROLLKEEPER_BUILD_REQUIRED=0.3.14
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


default_docbook_xsl=none
for d in \
      /usr/local/share/xsl/docbook \
      /usr/share/sgml/docbook/xsl-stylesheets*; do
    if test -d ${d}; then
        default_docbook_xsl=${d}
    fi
done
AC_ARG_WITH(
	docbook-xsl,
	[  --with-docbook-xsl=DIR    Where docbook-xsl stylesheets live [$default_docbook_xsl]],
	docbook_xsl_stylesheets=${withval},
	docbook_xsl_stylesheets=${default_docbook_xsl})

AC_SUBST(docbook_xsl_stylesheets)

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


dnl
dnl Internationalization
dnl

GETTEXT_PACKAGE=remus-audiostore
AC_SUBST(GETTEXT_PACKAGE)
AC_DEFINE_UNQUOTED(GETTEXT_PACKAGE,"$GETTEXT_PACKAGE", [The gettext package name])
ALL_LINGUAS="sv"
AM_GLIB_GNU_GETTEXT

AC_CONFIG_FILES(
setup.py
Makefile
db/Makefile
doc/Makefile
doc/xsl/Makefile
doc/xsl/fo/Makefile
doc/xsl/html/Makefile
doc/xml/project.ent
doc/manual/Makefile
doc/manual/C/Makefile
doc/manual/C/remus-audiostore-C.omf
po/Makefile.in
styles/param.xsl
styles/Makefile
)

AC_OUTPUT
