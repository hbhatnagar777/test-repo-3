"""
File for calculating the extents on remote machine without python . This will be packaged into exe
create_connection - Create connection with sqlite database
get_extent_count - get the extent count from DB
"""
import sys

try:
    import sqlite3
except ImportError as error:
    raise Exception('Failed to import sqlite3\nError: "{0}"'.format(error.msg))


def create_connection(path):
    """ create a database connection to the SQLite database
        specified by the db_file
    :return: Connection object or None
    """
    if not path:
        db_file = "no_db"
    else:
        db_file = path
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as err:
        print(err)
    return None


def get_extent_count():
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :return:
    """
    path = None
    if len(sys.argv) == 2:
        path = sys.argv[1]
    conn = create_connection(path)
    cur = conn.cursor()
    cur.execute("SELECT count(DeviceId) from LruExtents")
    rows = cur.fetchall()
    print(rows[0][0])


get_extent_count()
