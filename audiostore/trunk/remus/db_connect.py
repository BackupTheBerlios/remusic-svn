import MySQLdb.connections

__connect_map = {}
curr_db = None

def connect(host="localhost", user="user", passwd="", db="remus"):
    if __connect_map.has_key((host, user)):
        return __connect_map((host, user))
    else:
        conn = MySQLdb.connections.Connection(
            host=host, user=user,
            passwd=passwd, db=db)
        __connect_map[(host, user, db)] = conn
        return conn

def set_current_user(user, passwd):
    global curr_db
    curr_db = connect(user=user, passwd=passwd)
    
