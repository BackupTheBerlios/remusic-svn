## Process this file with automake to produce Makefile.in

bin_PROGRAMS = remus-player

remus_player_SOURCES = remus-player.cc

LDADD		= ${GST_LIBS} ${GNOME_VFS_LIBS}
LDFLAGS		= -g
AM_CXXFLAGS	= -g ${GST_CFLAGS} ${GNOME_VFS_CFLAGS} $(shell pkg-config --cflags gconf-2.0)
