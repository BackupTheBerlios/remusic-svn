XSLT = @XSLTPROC@

LANGS =     \
    en.xml  \
    sv.xml

all: ${LANGS}

%.xml: locale/%.xml
	$(XSLT) -o $@ --stringparam locale.file $@ xsl/xsl.xsl locale/en.xml
