#
# Build customized titlepage stylesheet
#

all: titlepage.templates.xsl

titlepage.templates.xsl: titlepage.templates.xml
	xsltproc /usr/local/share/xsl/docbook/template/titlepage.xsl $< > $@
