from datetime import datetime
import pandas as pd
import sqlite3
from sqlalchemy import create_engine

from data_ingestion import GetData


class StageData:
    """
        This class stages fully processed data treated from the data_ingestion module on to a postgresql database.

        class attributes:
            tablename1 & 2 (str): Names assigned to the tables created in the database
            data : invokes the class method GetData to extract data
            conn & engine (str): postgresql connection details
        """

    def __init__(self):
        self.data = GetData()
        # self.tablename1 = "postcode_data"
        # self.tablename2 = "customer_data"
        self.conn = sqlite3.connect(':memory:')

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS Customers ("
                "user_id       INTEGER PRIMARY KEY,"
                "email         TEXT NOT NULL UNIQUE,"
                "first_name    TEXT,"
                "last_name     TEXT,"
                "sex           TEXT,"
                "date_of_birth DATE"
            ")")
        cursor.execute("CREATE INDEX idx_users_email ON Customers(email)")

        cursor.execute(
            "CREATE TABLE IF NOT EXISTS Addresses ("
                "address_id  INTEGER PRIMARY KEY,"
                "user_id     INTEGER NOT NULL,"
                "street      TEXT,"
                "postcode    TEXT,"
                "valid_from  DATETIME NOT NULL,"
                "valid_to    DATETIME,"
                "FOREIGN KEY (user_id) REFERENCES Customers(user_id)"
            ")")
        cursor.execute("CREATE INDEX idx_addresses_user ON Addresses(user_id)")

        cursor.execute(
            "CREATE TABLE IF NOT EXISTS Postcode ("
                "objectid  INTEGER PRIMARY KEY,"
                "postcode  TEXT,"
                "usertype  INTEGER,"
                "oseast1m  INTEGER,"
                "osnrth1m  INTEGER,"
                "city      TEXT,"
                "country   TEXT,"
                "latitude  INTEGER,"
                "longitude INTEGER,"
                "region    TEXT"
            ")")
        self.conn.commit()
    
    def save_to_database(self):
        self.create_tables()

        data_dict = self.data.callmethods()
        postcode_data = data_dict["postcode_data"]
        postcode_data.to_sql("Postcode", self.conn, if_exists="append", index=False)


        customer_data = data_dict["customer_data"]
        customers = customer_data[['email', 'first_name', 'last_name', 'sex', 'date_of_birth']]
        customers.to_sql("Customers", self.conn, if_exists="append", index=False)
        
        customers_in_db = pd.read_sql_query("SELECT user_id, email FROM Customers", self.conn)
        addresses_df = pd.merge(customer_data, customers_in_db, on="email")
        addresses_df['valid_from'] = datetime.now().strftime('%Y-%m-%d')
        addresses_df['valid_to'] = None
        addresses_df = addresses_df[['user_id', 'street', 'postcode', 'valid_from', 'valid_to']]
        addresses_df.to_sql("Addresses", self.conn, if_exists="append", index=False)
        
    def query_table(self):
        # retrieved_df = pd.read_sql_query(f"SELECT * FROM Addresses", self.conn)

        df = pd.read_sql_query("SELECT p.region AS local_authority, COUNT(DISTINCT c.user_id) AS distinct_users FROM Customers c JOIN Addresses a ON c.user_id = a.user_id JOIN Postcode p ON a.postcode = p.postcode WHERE a.valid_to IS NULL GROUP BY p.region", self.conn)
        
        print(df)

        self.conn.close()

if __name__ == '__main__':
    sd = StageData()
    sd.save_to_database()
    sd.query_table()