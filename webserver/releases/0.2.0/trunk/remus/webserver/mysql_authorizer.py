"""Authorize users using the MySQL user table.
"""

import remus.database

class mysql_authorizer:

    def __init__(self, dbconn):
        self.dbconn = dbconn
        
    def authorize(self, auth_info):
        [username, password] = auth_info
        cursor = self.dbconn.cursor()
        cnt = cursor.execute(
            "SELECT PASSWORD(%s), Password FROM user WHERE User = %s",
            (password, username))

        if cnt:
            row = cursor.fetchone()
            if row[0] == row[1]:
                #remus.database.set_current_user(username, password)
                return True
            else:
                return False
        else:
            return False

        
