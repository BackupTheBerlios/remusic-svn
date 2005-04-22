all: titlepage.xsl

titlepage.xsl: titlepage.xml
	${XSLTPROC} -o $@ ${docbook_xsl_stylesheets}/template/titlepage.xsl \
		titlepage.xml
