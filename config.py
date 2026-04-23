import mysql.connector

def get_db():
    return mysql.connector.connect(
        host     = 'localhost',
        user     = 'root',
        password = 'root123',
        database = 'disaster_prep_db'
    )