import MySQLdb.connections

__connect_map = {}
curr_db = None

def connect(host="localhost", user="user", passwd="", db="remus"):
    key = (host, user, db)
    if __connect_map.has_key(key):
        return __connect_map[key]
    else:
        conn = MySQLdb.connections.Connection(
            host=host, user=user,
            passwd=passwd, db=db)
        __connect_map[key] = conn
        return conn

def set_current_user(user, passwd=""):
    global curr_db
    curr_db = connect(user=user, passwd=passwd)
    return curr_db
