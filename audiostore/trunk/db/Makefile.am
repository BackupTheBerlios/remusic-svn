#
# Generate files from the DB XML source file
#

include /usr/local/share/sqlml/sqlml.make

DB		= audiostore
DBXMLFILE	= ${DB}.xml
DBDOCFILE	= ${DB}-doc.xml
PYMODULE	= ../remus/${DB}/db_${DB}.py
SQLFILE		= ${DB}.sql
DOC		= ../doc/manual/C/db-${DB}.xml

DOTFILE		= ${DB}.dot
DOTGRAPH	= ../doc/manual/figures/${DB}.${GRAPHFORMAT}

DOCBOOK_XSLTPROC_ARGS = --stringparam dbfigure figures/${DB}.${GRAPHFORMAT} \
                        --stringparam topelement chapter

all: ${PYMODULE} ${SQLFILE} ${DOTGRAPH} ${DOC}

${PYMODULE}: ${DBXMLFILE}
	${TRANSFORM.sqlml.py} $<

${DOTGRAPH}: ${DOTFILE}
	${TRANSFORM.dot.${GRAPHFORMAT}} $<


${DOC}: ${DBDOCFILE}
#	Remove the <?xml ...?> header
	grep -v "<?xml" ${DBDOCFILE} > ${DOC}
