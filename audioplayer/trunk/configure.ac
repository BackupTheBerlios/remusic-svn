AC_INIT(remus-player,0.0.1)
AM_MAINTAINER_MODE
AM_INIT_AUTOMAKE
AC_CONFIG_SRCDIR(src/remus-player.cc)

AC_PROG_CC
AC_PROG_CXX
AC_STDC_HEADERS

dnl Now we're ready to ask for gstreamer libs and cflags
dnl And we can also ask for the right version of gstreamer
HAVE_GSTREAMER=no
GST_REQS=0.6.1

dnl start with 0.7
GST_MAJORMINOR=0.7
PKG_CHECK_MODULES(GST, \
	gstreamer-play-$GST_MAJORMINOR >= $GST_REQS \
	gstreamer-gconf-$GST_MAJORMINOR >= $GST_REQS,
	HAVE_GSTREAMER=yes,HAVE_GSTREAMER=no)

dnl try 0.6
if test "x$HAVE_GSTREAMER" = "xno"; then
	GST_MAJORMINOR=0.6
	PKG_CHECK_MODULES(GST, \
		gstreamer-play-$GST_MAJORMINOR >= $GST_REQS \
		gstreamer-gconf-$GST_MAJORMINOR >= $GST_REQS,
		HAVE_GSTREAMER=yes,HAVE_GSTREAMER=no)
fi

PKG_CHECK_MODULES(GNOME_VFS, gnome-vfs-2.0)

dnl Give error and exit if we don't have gstreamer
if test "x$HAVE_GSTREAMER" = "xno"; then
	AC_MSG_ERROR(you need gstreamer development packages installed !)
fi

AC_SUBST(GST_LIBS)
AC_SUBST(GST_CFLAGS)
AC_SUBST(GNOME_VFS_LIBS)
AC_SUBST(GNOME_VFS_CFLAGS)

AC_OUTPUT([
  Makefile 
  src/Makefile 
])
