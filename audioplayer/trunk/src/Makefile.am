## Process this file with automake to produce Makefile.in

bin_PROGRAMS = remus-player

remus_player_SOURCES = remus-player.cc remus-player-playlist.cc

LDADD		= ${GST_LIBS} ${GNOME_VFSMM_LIBS}
AM_LDFLAGS	= -g
AM_CXXFLAGS	= -g ${GST_CFLAGS} ${GNOME_VFSMM_CFLAGS} ${GCONFMM_CFLAGS}

