import sqlite3
import os
import utils

DB_PATH = str(os.getenv("DB_PATH"))

class DBManager:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()


    def fetch_all_data(self, table_name):
        self.cursor.execute(f"SELECT * FROM {table_name}")
        return self.cursor.fetchall()

    def initialize_failed_downloads_db(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS FAILED_DOWNLOADS (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                tracing_no TEXT,
                URL TEXT
            )
        ''')
        self.conn.commit()

    def initialize_failed_requests_db(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS FAILED_REQUESTS (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                URL TEXT,
                query_params TEXT,
                headers TEXT
            )
        ''')
        self.conn.commit()
    
    def remove_failed_download(self, tracing_no):
        self.cursor.execute(f"DELETE FROM FAILED_DOWNLOADS WHERE tracing_no = {tracing_no}")
        self.conn.commit()
        return f"Removed {tracing_no} from FAILED_DOWNLOADS table"


    def add_failed_download(self, tracing_no, url):
        self.initialize_failed_downloads_db()
        self.cursor.execute(f"INSERT INTO FAILED_DOWNLOADS (tracing_no, URL) VALUES (?, ?)", (tracing_no, url))
        self.conn.commit()
        return f"Added {tracing_no} to FAILED_DOWNLOADS table with ID {self.cursor.lastrowid}"

    def add_failed_request(self, url, query_params, headers):
        self.initialize_failed_requests_db()
        self.cursor.execute(f"INSERT INTO FAILED_REQUESTS (URL, query_params, headers) VALUES (?, ?, ?)", (url, query_params, headers))
        self.conn.commit()
        return f"Added {utils.construct_url(url, query_params)} to FAILED_REQUESTS table with ID {self.cursor.lastrowid}"

# data = DBManager(DB_PATH).fetch_all_data("processed_letters")
# print(data, len(data))

# print('https://codal.ir/DownloadFile.aspx?id=Gr6GlBw4YgJowKJJRs8r3w%3d%3d'.encode('utf-8'))
# print(data, len(data))

# DB = DBManager(DB_PATH)
# DB.add_failed_download(1090245, "https://codal.ir/Reports/DownloadFile.aspx?id=c%2bOYSQQQaQQQmsAyxd52H626fS6A%3d%3d")
# DB.remove_failed_download(1093288)