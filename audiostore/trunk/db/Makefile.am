#
# Generate files from the DB XML source file
#

# Tools
XSLTPROC	= @XSLTPROC@
DOT		= @DOT@

DB		= audiostore
DBXMLFILE	= ${DB}.xml
PYMODULE	= ../remus/${DB}/db_${DB}.py
SQLFILE		= ${DB}.sql

if HAVE_DOT
SIZE		= 7,10
DOTFILE		= ${DB}.dot
DOTGRAPH	= ../doc/${DB}.${GRAPHFORMAT}
GRAPHFORMAT	= png
endif

all: ${PYMODULE} ${SQLFILE} ${DOTGRAPH}

${PYMODULE}: ${DBXMLFILE}
	@echo "Building python database classes"
	@${XSLTPROC} -o $@ makepython.xsl ${DBXMLFILE}

${SQLFILE}: ${DBXMLFILE}
	@echo "Building SQL database file"
	@${XSLTPROC} -o $@ makesql.xsl ${DBXMLFILE}

${DOTFILE}: ${DBXMLFILE}
	@echo "Building Graphviz dot graph"
	@${XSLTPROC} -o $@ makedot.xsl ${DBXMLFILE}

${DOTGRAPH}: ${DOTFILE}
	@echo "Generating graph in ${GRAPHFORMAT} format"
	@${DOT} -Gsize="${SIZE}" -T${GRAPHFORMAT} -o $@ ${DOTFILE}

