#
# Build customized titlepage stylesheet
#

DOCBOOK_XSL	= /usr/local/share/xsl/docbook

all: titlepage.templates.xsl

titlepage.templates.xsl: titlepage.templates.xml
	xsltproc ${DOCBOOK_XSL}/template/titlepage.xsl titlepage.templates.xml > $@
