#
# Build customized titlepage stylesheet
#

DOCBOOK_XSL	= @DOCBOOK_XSL@

all: titlepage.templates.xsl

titlepage.templates.xsl: titlepage.templates.xml
	xsltproc @DOCBOOK_XSL@/template/titlepage.xsl $< > $@
