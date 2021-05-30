from mysql.connector import MySQLConnection, Error
from python_mysql_dbconfig import read_db_config

# Funcion que establece la conexion con la base de datos
def connect():

    db_config = read_db_config()
    conn = None
    try:
        print('Connecting to MySQL database...')
        conn = MySQLConnection(**db_config)

        if conn.is_connected():
            print('Connection established.')
        else:
            print('Connection failed.')

    except Error as error:
        print(error)
