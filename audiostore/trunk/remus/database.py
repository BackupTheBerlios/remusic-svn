"""Abstraction layer of an SQL database, keeping track of relations
between tables.
"""

class Table:
    "Describes an SQL table structure"

    def __init__(self, database, name, columns):
        self.database = database
        self.name = name
        self.columns = columns
        for column in columns:
            column.settable(self)
        self.setup_relations()


    def setup_relations(self):
        "Initialize relations between tables"
        self.relations = {}
        for column in self.columns:
            if issubclass(column.__class__, Relation):
                self.relations[column.relation.table] = column


class Column:
    "Describes a column in an SQL table"

    def __init__(self, name):
        self.name = name
        self.table = None


    def settable(self, table):
        self.table = table


class Relation(Column):
    "Column with a relation to another table"

    def __init__(self, name, column):
        """Create a relation column.

        Arguments:

          'name'   - column name
          'column' - column in foreign table to relate to
        """
        Column.__init__(self, name)
        self.relation = column


def query_tables(query, tables):
    "Insert the tables needed for the query into 'tables'."
    if hasattr(query, 'table') and query.table not in tables:
        tables.append(table)
    if hasattr(query, 'left'):
        query_tables(query.left, tables)
    if hasattr(query, 'right'):
        query_tables(query.right, tables)

    
class Select:
    """Collection of columns, and calculation of what tables need
    to be consulted to fetch these columns from the database,
    obeying the relational constraints
    """

    def __init__(self):
        self.__columns = []
        self.__tables = []


    def addcolumn(self, column):
        "Add column to the selection"
        self.__columns.append(column)
        if column.table not in self.__tables:
            self.__tables.append(column.table)


    def tables(self, query=None):
        """The set of tables which need to be consulted to fetch
        the set of columns"""
        if not query:
            return self.__tables
        else:
            tables = self.__tables[:]
            query_tables(query, tables)
            return tables


    def where(self, query=None, tables=None):
        """Construct an SQL where clause.

        Returns a tuple containing the clause as a string, and
        a tuple of arguments to pass to the 'cursor.execute'
        method."""
        relations = []
        tables = tables or self.tables()
        for table in tables:
            for reltable in tables:
                if table == reltable:
                    continue
                elif table.relations.has_key(reltable):
                    relations.append(table.relations[reltable])

        if relations:
            rels = [ "%s = %s" % (rel.name, rel.relation.name)
                     for rel in relations ]
            where_clause = "WHERE %s" % " AND ".join(rels)
        else:
            where_clause = ""

        if query:
            query, args = query.expr()
            if where_clause:
                where_clause += " AND "
            else:
                where_clause += "WHERE "

            where_clause += query
        else:
            args = ()

        return where_clause, args


    def select(self, query=None, order_by=None, group_by=None):
        "Return an SQL select statement"
        columns = ", ".join([ col.name for col in self.__columns ])
        tables = ", ".join([ tab.name for tab in self.tables() ])

        where_clause, args = self.where(query)
        
        if group_by:
            group_by = "GROUP BY " + ", ".join(group_by)
        else:
            group_by = ''

        if order_by:
            order_by = "ORDER BY " + ", ".join(order_by)
        else:
            order_by = ''

        sql = "SELECT %s FROM %s %s %s %s" % \
              (columns, tables, where_clause, group_by, order_by)

        return sql, args


def test():
    column1_1 = Column("col1_1")
    column1_2 = Column("col1_2")
    column1_3 = Column("col1_3")
    #
    table1 = Table("remus", "Foo", (column1_1, column1_2, column1_3))
    #
    column2_1 = Relation("col2_1", column1_1)
    column2_2 = Column("col2_2")
    #
    table2 = Table("remus", "Bar", (column2_1, column2_2))
    #
    table2.setup_relations()
    #
    select = Select()
    select.addcolumn(column1_2)
    select.addcolumn(column2_2)
    print select.select()
    
if __name__ == "__main__":
    test()
