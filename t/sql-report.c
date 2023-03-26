#include <assert.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/*
 * Define next query.
 */
const char master[] =
  "SELECT  type, name, tbl_name, rootpage "
  "FROM    sqlite_master "
  "WHERE   type in ('table', 'view') "
  "AND     name not like 'sqlite?_%' escape '?' "
  ;

const char *colnames[] = { "type", "name", "tbl_name", "rootpage" };
  
struct sysrow_t {
  char type[16];
  char name[32];
  char tbl_name[32];
  int rootpage;
};

int element_count( struct sysrow_t tgt );

#ifdef COPY_ROW_MAC
void
copy_row( struct sqlite3_stmt *stmt, struct sysrow_t *row );
#else 
void
copy_row( struct sqlite3_stmt *stmt, struct sysrow_t *row ) {
  int ordinal = 0;
  strcpy( row->type, sqlite3_column_text(stmt, ordinal++) );
  strcpy( row->name, sqlite3_column_text(stmt, ordinal++) );
  strcpy( row->tbl_name, sqlite3_column_text(stmt, ordinal++) );
  row->rootpage = sqlite3_column_int64(stmt, ordinal++);
}
#endif

void
print_row( const struct sysrow_t *row ) {
  printf( "%16s %32s %32s %d\n",
          row->type, 
          row->name, 
          row->tbl_name, 
          row->rootpage );
}

int main(int argc, char *argv[])
{
  sqlite3 *db;
  sqlite3_stmt *stmt;
  int erc;

  if( argc == 1 ) {
    errx(EXIT_FAILURE, "syntax: %s dbname", argv[0]);
  }

  if( (erc = access(argv[1], R_OK)) == -1 ) {
    err(EXIT_FAILURE, "dbname: %s", argv[0]);
  }

  /*
   * Open database.
   */
  if( (erc = sqlite3_open_v2(argv[1], &db, SQLITE_OPEN_READONLY, NULL))
      != SQLITE_OK ) {
    errx(EXIT_FAILURE, "%d: %s", __LINE__, sqlite3_errmsg(db));
  }

  /*
   * Prepare query, create statement handle.
   */
  if( (erc = sqlite3_prepare(db, master, -1, &stmt, NULL)) != SQLITE_OK ) {
    errx(EXIT_FAILURE, "%d: %s", __LINE__, sqlite3_errmsg(db));
  }

  {
    struct sysrow_t row;
    assert(element_count(row) <= sqlite3_column_count(stmt));
  }
  
  while( (erc = sqlite3_step(stmt)) == SQLITE_ROW ) {
    struct sysrow_t row;
    copy_row(stmt, &row);
    print_row(&row);
  }
  switch(erc) {
  case SQLITE_ROW:
    break;
  case SQLITE_DONE:
    break;
	  
  case SQLITE_MISUSE:
  case SQLITE_BUSY:
  case SQLITE_ERROR:
  default:
    errx(EXIT_FAILURE, "%s", sqlite3_errstr(erc));
  }

  return 0;
}
