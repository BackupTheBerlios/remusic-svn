#
# Generate files from the DB XML source file
#

include /usr/local/share/sqlml/sqlml.make

DB		= audiostore
DBXMLFILE	= ${DB}.xml
PYMODULE	= ../remus/${DB}/db_${DB}.py
SQLFILE		= ${DB}.sql

DOTFILE		= ${DB}.dot
DOTGRAPH	= ../doc/${DB}.${GRAPHFORMAT}

all: ${PYMODULE} ${SQLFILE} ${DOTGRAPH}

${PYMODULE}: ${DBXMLFILE}
	${TRANSFORM.sqlml.py} $<

${DOTGRAPH}: ${DOTFILE}
	${TRANSFORM.dot.${GRAPHFORMAT}} $<

