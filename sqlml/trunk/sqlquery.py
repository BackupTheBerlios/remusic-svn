"""SQL table abstraction.

This module defines classes to model SQL tables. It is normally
imported by generated modules from sqlml source files, which contains
descriptions of specific tables.
"""

__author__ = "Daniel Larsson <daniel.j.larsson@chello.se>"

__all__ = (
    'Table',
    'Column',
    'Relation',
    'PrimaryKey',
    'Function',
    'FuncBinaryOp',
    'Select',
    'AND',
    'OR',
    'LIKE',
    'REGEXP',
    'EQUAL',
    'GREATER_THAN',
    'LESS_THAN',
    'GREATER_EQUAL',
    'LESS_EQUAL',
    'SUBSTRING',
    'CONCAT',
    'SUM',
    'COUNT',
    'AVG',
    'MAX',
    'MIN',
    'VARIANCE',
    'STD',
    'STDDEV',
    'BIT_OR',
    'BIT_AND',
    'format_sql',
    )

try:
    import MySQLdb
    import MySQLdb.converters

    def literal(o):
        return MySQLdb.escape(o, MySQLdb.converters.conversions)
except ImportError:
    def literal(o):
        return repr(o)


# All classes defined herein are 'new-style' classes, allowing use of 'super()'
__metaclass__ = type

class Table:
    """Describes an SQL table.

    A table consists of a number of columns, some of which may be
    primary keys or relations to other tables.  Note that only a
    subset of possible SQL tables are supported.  Multi column keys,
    for instance, aren't supported.
    """

    def __init__(self, database, name, columns):
        """Create a new table description.

        Create a description of the table 'name' in the database
        'database', with the given sequence of columns.
        """
        # Initialize members
        self.primary_key = None
        self.database = database
        self.name = name
        self.columns = columns
        self.relations = {}

        # Make a dictionary of the columns as well for attribute access
        self.column_dict = {}
        for col in self.columns:
            self.column_dict[col.name] = col

        # Let columns know which table they're contained in
        for column in columns:
            column.settable(self)

        # Set up relation mappings (table -> column)
        self.setup_relations()

    def __getattr__(self, attr):
        """Provide access to columns as attributes.

        CAVEAT: Column names are shadowed by standard attributes.
        """
        try:
            return self.column_dict[attr]
        except KeyError:
            raise AttributeError, \
                  "%s instance has no attrbute '%s'" % \
                  (self.__class__.__name__, attr)

    def column(self, colname):
        """Column access function.

        More reliable than using attribute access notation.
        """
        return self.column_dict[colname]

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__,
                                self.name)

    def setprimary_key(self, column):
        "Make 'column' this table's primary key"
        self.primary_key = column

    def setup_relations(self):
        "Initialize relations between tables"
        self.relations = {}
        for column in self.columns:
            if issubclass(column.__class__, Relation):
                assert column.relation.table, \
                       "%s is not in a table yet" % column
                self.relations[column.relation.table] = column

    def reachable(self, table, visited=[]):
        """If we can reach 'table' through relations, return the
        table through which we can reach it.
        """
        for reltable, column in self.relations.items():
            if reltable == table:
                return table
            if reltable not in visited:
                if reltable.reachable(table, visited):
                    return reltable
                visited.append(reltable)
        return None

class Column:
    "Describes a column in an SQL table"

    def __init__(self, name):
        "Create a new column with name 'name'"
        self.name = name
        self.table = None

    def __repr__(self):
        tablename = self.table and self.table.name or "unknown"
        return "<%s: %s.%s>" % (self.__class__.__name__,
                                tablename,
                                self.name)

    # Mathematical operations are translated to select functions, not
    # actually calculated

    def __mul__(self, other):
        return FuncBinaryOp('*', self, other)

    def __rmul__(self, other):
        return FuncBinaryOp('*', other, self)

    def __add__(self, other):
        return FuncBinaryOp('+', self, other)

    def __radd__(self, other):
        return FuncBinaryOp('+', other, self)

    def __sub__(self, other):
        return FuncBinaryOp('-', self, other)

    def __rsub__(self, other):
        return FuncBinaryOp('-', other, self)

    def __div__(self, other):
        return FuncBinaryOp('/', self, other)

    def __rdiv__(self, other):
        return FuncBinaryOp('/', other, self)

    # Public methods

    def tables(self):
        """Return the tables referenced by this column.

        For normal columns, there's only one table.
        """
        return (self.table,)

    def canonical_name(self):
        "Column name prefixed by table name"
        assert self.table
        return "%s.%s" % (self.table.name, self.name)

    def settable(self, table):
        "Make me part of the table 'table'"
        self.table = table


class PrimaryKey(Column):
    "Primary key for table"

    def __init__(self, name):
        Column.__init__(self, name)

    def settable(self, table):
        """Make me part of the table 'table'

        In addition to Column.settable, also tell the table I'm the
        primary key.
        """
        Column.settable(self, table)
        table.setprimary_key(self)


class Relation(Column):
    "Column with a relation to another table's column"

    def __init__(self, name, column):
        """Create a relation column.

        Arguments:

          'name'   - column name
          'column' - column in foreign table to relate to
        """
        Column.__init__(self, name)
        self.relation = column


class Function:
    """Function call in select clause.

    SQL select clauses can not only contain column names, but also
    function calls, such as 'SUM', 'COUNT', etc. This class represents
    such functions.
    """

    def __init__(self, func, *columns):
        """Create a function 'column', with 'columns' as arguments.

        'columns' may contain Column instances, or literal values.

        Example:

        >>> sum = Function('SUM', 3, 4, 5)
        >>> print sum.canonical_name()
        SUM(3, 4, 5)

        Functions can be nested as well (here we're using the
        convenience functions instead of 'Function' directly):

        >>> f = SUBSTRING(CONCAT('Daniel', 'Larsson'), 7)
        >>> print f.canonical_name()
        SUBSTRING(CONCAT('Daniel', 'Larsson'), 7)
        """
        self.function = func
        self.columns = columns

    def canonical_name(self):
        columns = ", ".join([ hasattr(col, 'canonical_name')
                              and col.canonical_name()
                              or repr(col)
                              for col in self.columns ])
        return "%s(%s)" % (self.function, columns)


    def tables(self):
        """Returns the list of referenced tables, if any.

        Recursively collects referenced tables from the function's
        arguments. Note that any doubles aren't removed.

        Example:

        >>> c1 = Column('col1')
        >>> c2 = Column('col2')
        >>> t1 = Table('db', 'table1', (c1, c2))
        >>> c3 = Column('col3')
        >>> c4 = Column('col4')
        >>> t2 = Table('db', 'table2', (c3, c4))
        >>> sum = Function('SUM', c1, c2, c3, c4)
        >>> print sum.tables()
        (<Table: table1>, <Table: table1>, <Table: table2>, <Table: table2>)
        """
        # Get the tables from each column
        tables = [ col.tables()
                   for col in self.columns
                   if hasattr(col, "tables") ]

        # 'tables' is a nested list, unfold it
        import operator
        return reduce(operator.add, tables, ())


# Some SQL functions (far from all, use "Function" if the function you
# want to use is missing).

# --- String functions

def SUBSTRING(*args):
    return Function("SUBSTRING", *args)

def CONCAT(*args):
    return Function("CONCAT", *args)


# --- Group by functions

def SUM(*args):
    return Function("SUM", *args)

def COUNT(*args):
    return Function("COUNT", *args)

def AVG(*args):
    return Function("AVG", *args)

def MAX(*args):
    return Function("MAX", *args)

def MIN(*args):
    return Function("MIN", *args)

def VARIANCE(*args):
    return Function("VARIANCE", *args)

def STD(*args):
    return Function("STD", *args)

def STDDEV(*args):
    return Function("STDDEV", *args)

def BIT_OR(*args):
    return Function("BIT_OR", *args)

def BIT_AND(*args):
    return Function("BIT_AND", *args)


class FuncBinaryOp(Function):
    """Implements binary operators with infix notation.

    The base class 'Function' implements support for SQL functions,
    which use the 'func(args)' notation. This class supports infix
    operators, such as 'a * b'.
    """
    def __init__(self, op, left, right):
        """Create binary operator 'op' with operands 'left' and 'right'.

        Example:

        >>> op = FuncBinaryOp('+', 2, 3)
        >>> print op.canonical_name()
        (2 + 3)
        >>> op2 = FuncBinaryOp('*', op, 7)
        >>> print op2.canonical_name()
        ((2 + 3) * 7)
        """
        assert left and right
        Function.__init__(self, op, left, right)

    def canonical_name(self):
        left = hasattr(self.columns[0], 'canonical_name') \
               and self.columns[0].canonical_name() \
               or self.columns[0]
        right = hasattr(self.columns[1], 'canonical_name') \
                and self.columns[1].canonical_name() \
                or self.columns[1]
        return "(%s %s %s)" % (left, self.function, right)


class QueryBinaryOp:
    """Base class for binary operations

    Base class for expressing 'where'-clauses in SQL select
    statements.
    """
    def __init__(self, *operands):
        "Create new operation with two operands"
        self.operands = operands

    def __str__(self):
        """Returns the string representation of this query expression.
        
        String operands are converted using the 'literal' function.
        You might want to replace this function if your database
        interface module provides one.

        Example:
        
        >>> op = AND('spam', 'egg')
        >>> str(op)
        "('spam' AND 'egg')"
        >>> column1_1 = Column('col1_1')
        >>> column1_2 = Column('col1_2')
        >>> column1_3 = Column('col1_3')
        >>> table1 = Table('remus', 'Foo', (column1_1, column1_2, column1_3))
        >>> op = AND(EQUAL(column1_1, 'ni'), EQUAL(column1_2, 'shrubbery'), \
                     LESS_THAN(column1_3, 10))
        >>> str(op)
        "((Foo.col1_1 = 'ni') AND (Foo.col1_2 = 'shrubbery') AND (Foo.col1_3 < 10))"
        """
        import types

        operands = []
        for operand in self.operands:
            if isinstance(operand, Column):
                operand = operand.canonical_name()
            elif type(operand) in types.StringTypes:
                operand = literal(operand)
            else:
                operand = str(operand)
            operands.append(operand)

        return "(%s)" % (" %s " % self.OP).join(operands)


class AND(QueryBinaryOp):
    "AND operand"
    OP = "AND"

class OR(QueryBinaryOp):
    "OR operand"
    OP = "OR"

class LIKE(QueryBinaryOp):
    "LIKE operand"
    OP = "LIKE"

class REGEXP(QueryBinaryOp):
    "REGEXP operand"
    OP = "REGEXP"

class EQUAL(QueryBinaryOp):
    "Equality operand"
    OP = "="

class GREATER_THAN(QueryBinaryOp):
    "Greater than operand"
    OP = ">"

class LESS_THAN(QueryBinaryOp):
    "Less than operand"
    OP = "<"

class GREATER_EQUAL(QueryBinaryOp):
    "Greater or equal to operand"
    OP = ">="

class LESS_EQUAL(QueryBinaryOp):
    "Less or equal to operand"
    OP = "<="


def query_tables(query, tables):
    "Insert the tables needed for the query into 'tables'."
    if hasattr(query, 'table') and query.table not in tables:
        tables.append(query.table)
    if hasattr(query, 'operands'):
        for operand in query.operands:
            query_tables(operand, tables)

def query_columns(query, columns):
    "Insert all columns occurring in the query into 'columns'."
    if hasattr(query, 'table') and query not in columns:
        columns.append(query)
    if hasattr(query, 'operands'):
        for operand in query.operands:
            query_columns(operand, tables)

def connect_tables(tables, connected):
    for table in tables:
        for other_table in tables:
            if table == other_table or \
                   table in connected and other_table in connected:
                continue
            new_table = table.reachable(other_table)
            if new_table and new_table not in tables:
                tables.append(new_table)


class Select:
    """SQL select statement.
    
    Collection of columns, and calculation of what tables need
    to be consulted to fetch these columns from the database,
    obeying the relational constraints.

    >>> column1_1 = Column('col1_1')
    >>> column1_2 = Column('col1_2')
    >>> column1_3 = Column('col1_3')
    >>> table1 = Table('remus', 'Foo', (column1_1, column1_2, column1_3))
    >>> column2_1 = Relation('col2_1', column1_1)
    >>> column2_2 = Column('col2_2')
    >>> table2 = Table('remus', 'Bar', (column2_1, column2_2))

    >>> select = Select()
    >>> select.addcolumn(column1_2)
    >>> select.addcolumn(column2_2)
    >>> print format_sql(select.select().strip())
    SELECT
        Foo.col1_2, Bar.col2_2
    FROM
        Foo, Bar
    WHERE
        Bar.col2_1 = Foo.col1_1
    >>> query = AND(EQUAL(column2_2,'kalle'), EQUAL(column1_3, 'nisse'))
    >>> select = Select()
    >>> select.addcolumn(column1_2)
    >>> sql = select.select(query=query, group_by=(column2_2,),\
                            order_by=(column1_2,))
    >>> print format_sql(sql)
    SELECT
        Foo.col1_2
    FROM
        Foo, Bar
    WHERE
        Bar.col2_1 = Foo.col1_1 AND ((Bar.col2_2 = 'kalle') AND (Foo.col1_3 = 'nisse'))
    GROUP BY
        Bar.col2_2
    ORDER BY
        Foo.col1_2
    >>> column1_1 = Column('col1_1')
    >>> column1_2 = Column('col1_2')
    >>> table1 = Table('remus', 'Foo', (column1_1, column1_2))
    >>> column2_1 = Relation('col2_1', column1_1)
    >>> column2_2 = Column('col2_2')
    >>> table2 = Table('remus', 'Bar', (column2_1, column2_2))
    >>> column3_1 = Relation('col3_1', column2_2)
    >>> column3_2 = Column('col3_2')
    >>> table3 = Table('remus', 'Spam', (column3_1, column3_2))
    >>> select = Select()
    >>> select.addcolumn(column1_1)
    >>> select.addcolumn(column3_2)
    >>> print table3.reachable(table1)
    <Table: Bar>
    >>> print format_sql(select.select().strip())
    SELECT
        Foo.col1_1, Spam.col3_2
    FROM
        Foo, Spam, Bar
    WHERE
        Spam.col3_1 = Bar.col2_2 AND Bar.col2_1 = Foo.col1_1
    """

    MAX_LOOP = 4

    def __init__(self):
        self.__columns = []
        self.__tables = []


    def addcolumn(self, column):
        "Add column to the selection"
        self.__columns.append(column)
        if hasattr(column, 'tables'):
            tables = column.tables()
            for table in tables:
                if table not in self.__tables:
                    self.__tables.append(table)


    def select(self, query=None, order_by=None, group_by=None):
        """Return an SQL select statement.

        Based on the columns added to this select, and the optional
        'query' argument, an SQL statement is returned with the
        correct tables and relational constraints added.
        """
        columns = ", ".join([ hasattr(col, 'canonical_name')
                              and col.canonical_name()
                              or str(col)
                              for col in self.__columns ])

        tables = self.gettables(query)
        where_clause = self.__where(query, tables)
        tables = ", ".join([ tab.name for tab in tables ])
        

        if group_by:
            try:
                group_by = [ isinstance(field, Column)
                             and field.canonical_name()
                             or field
                             for field in group_by ]
            except TypeError:
                group_by = (isinstance(group_by, Column) \
                            and group_by.canonical_name() \
                            or group_by,)

            group_by = "GROUP BY " + ", ".join(group_by)
        else:
            group_by = ''

        if order_by:
            order_by = [ isinstance(field, Column)
                         and field.canonical_name()
                         or field
                         for field in order_by ]
            order_by = "ORDER BY " + ", ".join(order_by)
        else:
            order_by = ''

        sql = "SELECT %s FROM %s %s %s %s" % \
              (columns, tables, where_clause, group_by, order_by)

        return sql


    def gettables(self, query=None):
        """The set of tables which need to be consulted to fetch
        the set of columns"""
        if not query:
            return self.__tables
        else:
            tables = self.__tables[:]
            query_tables(query, tables)
            return tables


    def __where(self, query=None, tables=None):
        """Construct an SQL where clause.

        Returns a tuple containing the clause as a string, and
        a tuple of arguments to pass to the 'cursor.execute'
        method."""

        # 'grouped' will contain all tables we can reach from
        # the first table in the list through the relations
        # found.
        tables = tables or self.gettables(query)
        grouped = []
        relations = []
        loops = 0
        while len(grouped) != len(tables) and loops < self.MAX_LOOP:
            for table in tables:
                for reltable in tables:
                    if table == reltable:
                        continue
                    elif table.relations.has_key(reltable):
                        if table.relations[reltable] not in relations:
                            relations.append(table.relations[reltable])
                            if not grouped:
                                grouped.append(table)
                                grouped.append(reltable)
                            elif table in grouped and reltable not in grouped:
                                grouped.append(reltable)
                            elif reltable in grouped and table not in grouped:
                                grouped.append(table)

            if len(grouped) != len(tables):
                # If 'grouped' and 'tables' aren't equal (equal
                # meaning containing the same elements, regardless of
                # order, i.e.  viewed as sets), we're missing some
                # indirect relations likely, and the SQL query will
                # create a cartesian product between some tables.
                # This is usually not what was intended, so lets try
                # find if we can "close" the gap via another table,
                # and adding relational constraints between the
                # existing tables, and this new one.
                connect_tables(tables, grouped)

            loops += 1

        if relations:
            rels = [ "%s = %s" % (rel.canonical_name(),
                                  rel.relation.canonical_name())
                     for rel in relations ]
            where_clause = "WHERE %s" % " AND ".join(rels)
        else:
            where_clause = ""

        if query:
            query = str(query)
            if where_clause:
                where_clause += " AND "
            else:
                where_clause += "WHERE "

            where_clause += query

        return where_clause


#
# Format SQL strings, basically just to make the docstring examples
# have less long lines.
#
def format_sql(sql):
    """Splits a SQL statement into multiple lines.

    >>> print format_sql('SELECT foo FROM bar')
    SELECT
        foo
    FROM
        bar
    >>> print format_sql('SELECT foo FROM bar WHERE a=b ORDER BY c')
    SELECT
        foo
    FROM
        bar
    WHERE
        a=b
    ORDER BY
        c
    """
    def find_part(sql, part):
        import re
        match = re.search(r"(%s) (.*)" % part, sql)
        if match:
            formatted = "\n%s\n    %s" % (match.group(1),
                                          match.group(2).strip())
            return sql[:match.start()], formatted
        else:
            return sql, ''

    # Look for parts right to left
    sql, order_by = find_part(sql, "ORDER BY")
    sql, group_by = find_part(sql, "GROUP BY")
    sql, where = find_part(sql, "WHERE")
    sql, from_part = find_part(sql, "FROM")
    sql, select = find_part(sql, "SELECT")
    return select[1:] + from_part + where + group_by + order_by
    

def testsuite():
    import doctest
    import sqlquery

    return doctest.DocTestSuite(sqlquery)
    
def _test():
    import unittest
    unittest.main(defaultTest="testsuite")


if __name__ == "__main__":
    _test()
