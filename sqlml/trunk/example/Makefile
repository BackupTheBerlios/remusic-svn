#include /usr/local/share/sqlml/sqlml.make
include  ../sqlml.make

DB		= orderdb
DB_USER 	= root
DB_PASSWD	=

ifneq "${DB_PASSWD}" ""
    DB_PW_ARG	=  -p ${DB_PASSWD}
endif

all: test

.populate: ${DB}.sql populate.sql
	mysql -u ${DB_USER} ${DB_PW_ARG} < ${DB}.sql
	mysql -u ${DB_USER} ${DB_PW_ARG} < populate.sql
	touch $@

test: .populate ${DB}.py
	python test.py

graph: ${DB}.png

doc: graph ${DB}-doc.xml

clean:
	-rm -f *~ *.pyc *.pyo
	-rm -f ${DB}.sql ${DB}.py ${DB}.png ${DB}-doc.xml
