
XSLTPROC	= @XSLTPROC@
DOCBOOK_XSL	= /usr/local/share/xsl/docbook

all: titlepage.xsl

titlepage.xsl: titlepage.xml
	${XSLTPROC} -o $@ ${DOCBOOK-XSL}/template/titlepage.xsl titlepage.xml
