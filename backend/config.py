import mysql.connector

def get_db():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root123",
            database="disaster_prep_db",
            autocommit=False
        )
        return connection
    except Exception as e:
        print(f"Database connection error: {e}")
        raise e