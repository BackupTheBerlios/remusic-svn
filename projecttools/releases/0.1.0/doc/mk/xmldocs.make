#
# No modifications of this Makefile should be necessary.
#
# To use this template:
#     1) Define: figdir, docname, lang, omffile, and entities in
#        your Makefile.am file for each document directory,
#        although figdir, omffile, and entities may be empty
#     2) Make sure the Makefile in (1) also includes 
#	 "include $(top_srcdir)/doc/xmldocs.make" and
#	 "dist-hook: app-dist-hook".
#     3) Optionally define 'entities' to hold xml entities which
#        you would also like installed
#     4) Figures must go under $(figdir)/ and be in PNG format
#     5) You should only have one document per directory 
#     6) Note that the figure directory, $(figdir)/, should not have its
#        own Makefile since this Makefile installs those figures.
#
# example Makefile.am:
#   figdir = figures
#   docname = scrollkeeper-manual
#   lang = C
#   omffile=scrollkeeper-manual-C.omf
#   entities = fdl.xml
#   include $(top_srcdir)/doc/xmldocs.make
#   dist-hook: app-dist-hook
#
# About this file:
#	This file was taken from scrollkeeper_example2, a package illustrating
#	how to install documentation and OMF files for use with ScrollKeeper 
#	0.3.x and 0.4.x.  For more information, see:
#		http://scrollkeeper.sourceforge.net/
#	Version: 0.1.2 (last updated: March 20, 2002)
#


# ************* Begin of section some packagers may need to modify  **************
# This variable (docdir) specifies where the documents should be installed.
# This default value should work for most packages.
# docdir = $(datadir)/@PACKAGE@/doc/$(docname)/$(lang)
docdir = $(datadir)/gnome/help/remus/$(lang)

# **************  You should not have to edit below this line  *******************
xml_files = $(entities) $(docname).xml
styledir = $(top_srcdir)/doc/xsl/images

# Convert xml to html with xsltproc
# xsltproc   -o outputdir/ /usr/share/sgml/docbook/xsl-stylesheets/html/chunk.xsl filename.xml
convert-html: 
	$(mkinstalldirs) $(docname).html; \
	for file in $(docname).xml; do \
	 xsltproc -o $(docname).html/ --param use.id.as.filename 1 \
	 $(top_srcdir)/doc/xsl/html/general-customization.xsl $(srcdir)/$$file; \
	done

convert-fo:
	for file in $(docname).xml; do \
	 xsltproc -o $(docname).fo --param use.id.as.filename 1 \
	 $(top_srcdir)/doc/xsl/fo/general-customization.xsl $(srcdir)/$$file; \
	done

convert-pdf: convert-fo
#	for file in $(docname).fo; do \
#	 fop -fo $$file -pdf $${file%.*}.pdf; \
#	done
	for file in $(docname).fo; do \
	 pdftex --interaction nonstopmode "&pdfxmltex" $$file; \
	done

EXTRA_DIST = $(xml_files) $(omffile)
CLEANFILES = omf_timestamp $(docname).html/*.html $(docname).fo $(docname).pdf

# If the following file is in a subdir (like help/) you need to add that to the path
include $(top_srcdir)/doc/mk/omf.make

all: omf convert-html convert-pdf

#$(docname).xml: $(entities)
#	-ourdir=`pwd`;  \
#	cd $(srcdir);   \
#	cp $(entities) $$ourdir

app-dist-hook:
	if test "$(figdir)"; then \
	  $(mkinstalldirs) $(distdir)/$(figdir); \
	  for file in $(srcdir)/$(figdir)/*.png; do \
	    basefile=`echo $$file | sed -e  's,^.*/,,'`; \
	    $(INSTALL_DATA) $$file $(distdir)/$(figdir)/$$basefile; \
	  done \
	fi

install-data-local:
	$(mkinstalldirs) $(DESTDIR)$(docdir)
	for file in $(xml_files); do \
	  cp $(srcdir)/$$file $(DESTDIR)$(docdir); \
	done
	  $(mkinstalldirs) $(DESTDIR)$(docdir)/$(docname); \
	  for file in $(docname).html/*.html; do \
	    basefile=`echo $$file | sed -e  's,^.*/,,'`; \
	    $(INSTALL_DATA) $$file $(DESTDIR)$(docdir)/$(docname)/$$basefile; \
	  done
	if test "$(figdir)"; then \
	  $(mkinstalldirs) $(DESTDIR)$(docdir)/$(figdir); \
	  $(mkinstalldirs) $(DESTDIR)$(docdir)/$(docname)/$(figdir); \
	  for file in $(srcdir)/$(figdir)/*.png; do \
	    basefile=`echo $$file | sed -e  's,^.*/,,'`; \
	    $(INSTALL_DATA) $$file $(DESTDIR)$(docdir)/$(figdir)/$$basefile; \
	    $(INSTALL_DATA) $$file $(DESTDIR)$(docdir)/$(docname)/$(figdir)/$$basefile; \
	  done \
	fi
	  $(mkinstalldirs) $(DESTDIR)$(docdir)/$(docname)/stylesheet; \
	  for file in $(styledir)/*.png; do \
	    basefile=`echo $$file | sed -e  's,^.*/,,'`; \
	    $(INSTALL_DATA) $$file $(DESTDIR)$(docdir)/$(docname)/stylesheet/$$basefile; \
	  done

install-data-hook: install-data-hook-omf

uninstall-local: uninstall-local-doc uninstall-local-omf

uninstall-local-doc:
	-rm -f $(DESTDIR)$(docdir)/help-search-index.db
	-if test "$(figdir)"; then \
	  for file in $(srcdir)/$(figdir)/*.png; do \
	    basefile=`echo $$file | sed -e  's,^.*/,,'`; \
	    rm -f $(docdir)/$(figdir)/$$basefile; \
	    rm -f $(docdir)/$(docname)/$(figdir)/$$basefile; \
	  done; \
	  rmdir $(DESTDIR)$(docdir)/$(figdir); \
	  rmdir $(DESTDIR)$(docdir)/$(docname)/$(figdir); \
	fi
	-for file in $(styledir)/*.png; do \
	    basefile=`echo $$file | sed -e  's,^.*/,,'`; \
	    rm -f $(docdir)/$(docname)/stylesheet/$$basefile; \
	  done; \
	  rmdir $(DESTDIR)$(docdir)/$(docname)/stylesheet
	-for file in $(srcdir)/$(docname)/*.html; do \
	    basefile=`echo $$file | sed -e  's,^.*/,,'`; \
	    rm -f $(docdir)/$(docname)/$$basefile; \
	  done; \
	  rmdir $(DESTDIR)$(docdir)/$(docname)
	-for file in $(xml_files); do \
	  rm -f $(DESTDIR)$(docdir)/$$file; \
	done
	-rmdir $(DESTDIR)$(docdir)
	-rmdir $(DESTDIR)$(datadir)/gnome/help/audiostore

