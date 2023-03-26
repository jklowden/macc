CPPFLAGS = -std=c11
CFLAGS = -g -O0

FAKE_H = ../3rd/pycparser/utils/fake_libc_include

# Find all #include files mentioned, and include them explicitly on
# the command line during post-macro compilation. The definitions are
# removed by macc.py.
INC = $(shell awk -F '[""<>]' '/#include/ { print $$2 }' $1 	\
	| sed 's/^/-include /')

.SUFFIXES: .ms .pdf

.PHONY: all t doc test

all: t/simple t/sql-report

t/simple: t/simple.c
	$(CC) -E -I $(FAKE_H) $^ > $@.i
	./macc.py -a $@.ast $@.i > $@.i.c
	$(CC) -o$@ $(call INC,$<) $@.i.c

t/sql-report: t/sql-report.c
	$(CC) -E -DCOPY_ROW_MAC -I $(FAKE_H) $^ > $@.i
	PYTHONPATH=$(PWD)/t \
	./macc.py -a $@.ast -m sql-report $@.i > $@.i.c
	$(CC) -o$@ -DCOPY_ROW_MAC $(CPPFLAGS) $(CFLAGS) \
		-include err.h -include sqlite3.h $(call INC,$<) \
	$@.i.c -lsqlite3

doc:	doc/macc.pdf



test: t/sql-report t/db
	$< t/db

t/db:
	sqlite3 -column -header t/db "create table T( a int, b text ); \
				      insert into T values \
					( 1, 'a' ),  \
					( 2, 'b' ),  \
					( 3, 'c' ); "
.ms.pdf:
	groff -ms -pte -Tpdf $^ > $@~
	@mv $@~ $@
