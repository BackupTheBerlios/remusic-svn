LANGS =     \
    en.xml  \
    sv.xml

all: ${LANGS}

%.xml: locale/%.xml
	$(XSLTPROC) -o $@ --stringparam locale.file $@ xsl/xsl.xsl \
		locale/en.xml
