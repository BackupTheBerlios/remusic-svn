
import MySQLdb.connections

from sqlquery import *
import orderdb


HOST = 'localhost'
USER = 'root'
PASSWD = ''
DB = 'orderdb'


def test():
    # Create DB connection
    conn = MySQLdb.connections.Connection(
        host=HOST, user=USER, passwd=PASSWD, db=DB)

    # Create queries using the sqlml module, and our generated module
    # Notice that column names are prefixed with the table name!
    select = Select()
    select.addcolumn(orderdb.items_name)
    select.addcolumn(orderdb.items_price)
    select.addcolumn(orderdb.itemorders_quantity)
    
    # Look for an order
    person = "Michael"
    query = EQUAL(orderdb.orders_person, person)
    sql = select.select(query=query)

    print "Running the following SQL:"
    print format_sql(sql)
    print '-' * 40

    cursor = conn.cursor()
    cursor.execute(sql)
    print "%s ordered:" % person
    for name, price, quantity in cursor:
        print "   %s %s @ %s" % (quantity, name, price)
    print
    print


    # We can also use SQL functions as columns.  To enable the sqlml
    # module to still be able to calculate which tables to query, we
    # can't add the function call as a pure string, since it needs to
    # know which columns we're accessing.  Mathematical operations can
    # be expressed using standard Python notation.

    select = Select()
    select.addcolumn(SUM(orderdb.items_price * orderdb.itemorders_quantity))
    sql = select.select(query=query)

    print "Running the following SQL:"
    print format_sql(sql)
    print '-' * 40

    cursor.execute(sql)
    print "Total cost for %s's order:" % person,
    for sum in cursor:
        print "%s" % sum


    # Nesting functions work as well. Some SQL functions have
    # convenience functions defined, for others, this examples shows
    # how to include them in the SQL query.

    def RPAD(*args):
        return Function("RPAD", *args)


    select = Select()
    select.addcolumn(
        SUBSTRING(
            MIN(
                CONCAT(
                    RPAD(
                        orderdb.items_price * orderdb.itemorders_quantity,
                        6,
                        ' '
                    ),
                    orderdb.items_name)),
            7)
        )
    sql = select.select(query=query)

    print "Running the following SQL:"
    print format_sql(sql)
    print '-' * 40

    cursor.execute(sql)
    print "Result of complex query:",
    for sum in cursor:
        print "%s" % sum

test()
