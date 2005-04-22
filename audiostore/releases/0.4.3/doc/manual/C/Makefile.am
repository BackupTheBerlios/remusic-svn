figdir = figures
docname = manual
lang = C
omffile = remus-audiostore-C.omf
entities = \
	fdl-appendix.xml \
	legal.xml \
	preface.xml \
	overview.xml \
	using.xml \
	db-audiostore.xml \
	project.ent
figures = \
	$(figdir)/audiostore.png

entity_dir = ../../xml

convert-html: ${entities} $(figdir)/audiostore.png $(figdir)/.copyparent

convert-pdf: ${entities} $(figdir)/audiostore.png $(figdir)/.copyparent

fdl-appendix.xml: ${entity_dir}/fdl-appendix.xml
	cp ${entity_dir}/fdl-appendix.xml $@

legal.xml: ${entity_dir}/legal.xml
	cp ${entity_dir}/legal.xml $@

project.ent: ${entity_dir}/project.ent
	cp ${entity_dir}/project.ent $@

${entity_dir}/project.ent: ${entity_dir}/project.ent.in $(top_builddir)/config.status
	cd $(top_builddir) && $(SHELL) ./config.status doc/xml/$$(basename $@)

include $(top_srcdir)/doc/mk/xmldocs.make

Makefile.in: $(top_srcdir)/doc/mk/xmldocs.make

dist-hook: app-dist-hook

$(figdir)/audiostore.png: $(figdir)
	cd $(top_srcdir)/db; \
	${MAKE} DOTGRAPH=$(PWD)/$@ $(PWD)/$@

$(figdir):
	mkdir $@

$(figdir)/.copyparent: $(figdir)
	for file in $$(ls ../$(figdir)); do \
	    [ -f $(figdir)/$$file ] || cp ../$(figdir)/$$file $(figdir); \
	done
	touch $@
