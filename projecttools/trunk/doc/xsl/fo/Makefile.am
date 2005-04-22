#
# Build customized titlepage stylesheet
#

all: titlepage.templates.xsl

titlepage.templates.xsl: titlepage.templates.xml
	${XSLTPROC} ${docbook_xsl_stylesheets}/template/titlepage.xsl \
	    titlepage.templates.xml > $@
