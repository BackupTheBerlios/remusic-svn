figdir = figures
docname = manual
lang = C
omffile = remus-audiostore-C.omf
entities = \
	fdl-appendix.xml \
	legal.xml \
	project.ent
figures = \
	$(figdir)/audiostore.png

convert-html: ${entities}

fdl-appendix.xml: ../../fdl-appendix.xml
	cp ../../fdl-appendix.xml $@

legal.xml: ../../legal.xml
	cp ../../legal.xml $@

project.ent: ../../project.ent
	cp ../../project.ent $@

include $(top_srcdir)/doc/xmldocs.make

dist-hook: app-dist-hook

$(figdir)/audiostore.png:
	cd $(top_src_dir)/db; \
	${MAKE} DOTGRAPH=$@ $@
