
XSLTPROC	= @XSLTPROC@
DOCBOOK-XSL	= /usr/local/share/xsl/docbooc

titlepage.xsl: titlepage.xml
	${XSLTPROC} -o $@ ${DOCBOOK-XSL}/template/titlepage.xsl titlepage.xml
