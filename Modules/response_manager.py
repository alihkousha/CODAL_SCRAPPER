import requests
import json
import utils
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
import threading
import datetime

# Define constants for limiting and retries
MAX_RETRIES = int(os.getenv("MAX_RETRIES"))
BACKOFF_FACTOR = float(os.getenv("BACKOFF_FACTOR"))
MAX_WORKERS = int(os.getenv("MAX_WORKERS"))
DESIRED_CHUCKS = int(os.getenv("DESIRED_CHUCKS"))
PATH = os.getenv("PATH").split(':')[0]
DB_PATH = os.getenv("DB_PATH")

class ResponseHandler:
    
    lock  = threading.Lock()
    
    def __init__(self, response : requests.models.Response):
        self.response = response
    
    def process_response(self, tracingNO : str = '', type = 'PDF'):
        if self.response.headers['Content-Type'].split(";")[0] == 'application/json':
            content : dict[str, str | list[dict[str, str | bool]]] = json.loads(self.response.content)
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executer:
                features = [executer.submit(ResponseHandler.save_letter_to_database, utils.letter_handler(letter)) for letter in content['Letters']]

        elif self.response.headers['Content-Type'].split(";")[0] == 'text/html':
            parser = utils.MyHTMLParser()
            parser.feed(self.response.content.decode('utf-8'))
            data = ["https://codal.ir/Reports/" + attachment for attachment in parser.onclick_attributes]
            ResponseHandler.save_attachments_to_database(tracingNO, data)

        else:
            letter = ResponseHandler.get_letter_by_tracing_no(tracingNO)
            title = letter[1]
            company_name = letter[2]
            path = utils.path_finder(self.response, title, company_name, type)
            with open(path, 'wb') as f:
                f.write(self.response.content)
            f.close()
            print(f'Successfully saved response of Letter : "{title}" at "{path}"')
            return

    def __repr__(self) -> str:
        return f"ResponseHandler({self.response.url})"

    @classmethod
    def initialize_database(cls, db_path : str = DB_PATH):
        try:
            cls.conn = sqlite3.connect(db_path)
        except Exception as e:
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            with open(db_path, 'w') as f:
                f.close()
            cls.conn = sqlite3.connect(db_path)
        cls.cursor = cls.conn.cursor()
        cls.cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_letters (
                tracing_no TEXT PRIMARY KEY,
                title TEXT,
                company_name TEXT,
                attachment_url TEXT,
                pdf_url TEXT,
                excel_url TEXT,
                attachments_files TEXT,
                date_created TIMESTAMP,
                date_pdf_downloaded TIMESTAMP,
                date_attachments_downloaded TIMESTAMP
            )
        ''')
        cls.conn.commit()
        return cls.conn, cls.cursor
    
    @classmethod
    def close_db(cls):
        cls.cursor.close()
        cls.conn.close()
    
    @classmethod
    def close_desired_db(cls, conn, cursor):
        cursor.close()
        conn.close()

    @classmethod
    def save_letter_to_database(cls, letter):
        try:
            ResponseHandler.lock.acquire(True)
            conn, cursor = cls.initialize_database()
            cursor.execute('''
                INSERT OR IGNORE INTO processed_letters
                (tracing_no, title, company_name, attachment_url, pdf_url, excel_url, date_created)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (str(letter['TracingNo']), letter['Title'], letter['CompanyName'], letter['AttachmentUrl'], 
                letter['PdfUrl'], letter['ExcelUrl'], datetime.datetime.now().replace(microsecond=0)))
            conn.commit()
            cls.close_desired_db(conn, cursor)
        finally:
            ResponseHandler.lock.release()
    
    @classmethod
    def save_attachments_to_database(cls, tracing_no, attachments):
        try:
            ResponseHandler.lock.acquire(True)
            conn, cursor = cls.initialize_database()
            cursor.execute('''
                UPDATE processed_letters
                SET attachments_files=?
                WHERE tracing_no=?
            ''', (json.dumps(attachments), tracing_no))
            conn.commit()
            cls.close_desired_db(conn, cursor)
        finally:
            ResponseHandler.lock.release()
    
    @classmethod
    def get_processed_letters(cls):
        try:
            ResponseHandler.lock.acquire(True)
            conn, cursor = cls.initialize_database()
            cursor.execute('SELECT * FROM processed_letters')
            data = cursor.fetchall()
            cls.close_desired_db(conn, cursor)
        finally:
            ResponseHandler.lock.release()
        return data

    @classmethod
    def get_letter_by_tracing_no(cls, tracing_no):
        try:
            ResponseHandler.lock.acquire(True)
            conn, cursor = cls.initialize_database()
            cursor.execute('''
                SELECT * FROM processed_letters
                WHERE tracing_no=?
            ''', (tracing_no,))
            data = cursor.fetchone()
            cls.close_desired_db(conn, cursor)
        finally:
            ResponseHandler.lock.release()
        
        return data

    @classmethod
    def get_letters_by_title(cls, title):
        try:
            ResponseHandler.lock.acquire(True)
            conn, cursor = cls.initialize_database()
            cursor.execute('''
                SELECT * FROM processed_letters
                WHERE title=?
            ''', (title,))
            data = cursor.fetchall()
            cls.close_desired_db(conn, cursor)
        finally:
            ResponseHandler.lock.release()
        return data

    @classmethod
    def get_letters_by_company_name(cls, company_name):
        try:
            ResponseHandler.lock.acquire(True)
            conn, cursor = cls.initialize_database()
            cursor.execute('''
                SELECT * FROM processed_letters
                WHERE company_name=?
            ''', (company_name,))
            data = cursor.fetchall()
            cls.close_desired_db(conn, cursor)
        finally:
            ResponseHandler.lock.release()
        return data

    @classmethod
    def get_attachments_from_database(cls):
        try:
            ResponseHandler.lock.acquire(True)
            conn, cursor = cls.initialize_database()
            cursor.execute('''
                SELECT tracing_no, attachment_url 
                FROM processed_letters
                WHERE attachment_url IS NOT '' AND date_attachments_downloaded IS NULL
            ''')
            data = cursor.fetchall()
            cls.close_desired_db(conn, cursor)
        finally:
            ResponseHandler.lock.release()
        return data

    
    @classmethod
    def get_attachments_files_from_database(cls):
        try:
            ResponseHandler.lock.acquire(True)
            conn, cursor = cls.initialize_database()
            cursor.execute('''
                SELECT tracing_no, attachments_files FROM processed_letters
                WHERE attachments_files IS NOT NULL AND date_attachments_downloaded IS NULL
                ''')
            data = cursor.fetchall()
            cls.close_desired_db(conn, cursor)
        finally:
            ResponseHandler.lock.release()
        return data

    @classmethod
    def get_pdf_from_database(cls):
        try:
            ResponseHandler.lock.acquire(True)
            conn, cursor = cls.initialize_database()
            cursor.execute('''
                SELECT tracing_no, pdf_url FROM processed_letters
                WHERE pdf_url != '' AND date_pdf_downloaded IS NULL
            ''')
            data = cursor.fetchall()
            cls.close_desired_db(conn, cursor)
        finally:
            ResponseHandler.lock.release()
        return data

    @classmethod
    def update_letter_in_database(cls, tracing_no, new_data):
        try:
            ResponseHandler.lock.acquire(True)
            conn, cursor = cls.initialize_database()
            cursor.execute('''
                UPDATE processed_letters
                SET title=?, company_name=?, attachment_url=?, pdf_url=?, excel_url=?
                WHERE tracing_no=?
            ''', (new_data['Title'], new_data['CompanyName'], new_data.get('AttachmentUrl', ''), new_data.get('PdfUrl', ''), new_data.get('ExcelUrl', ''), tracing_no))
            conn.commit()
            cls.close_desired_db(conn, cursor)
        finally:
            ResponseHandler.lock.release()        

    @classmethod
    def update_letter_download_date_in_database(cls, tracing_no):
        try:
            ResponseHandler.lock.acquire(True)
            conn, cursor = cls.initialize_database()
            cursor.execute('''
                UPDATE processed_letters
                SET date_pdf_downloaded=?
                WHERE tracing_no=?
            ''', (datetime.datetime.now().replace(microsecond=0), tracing_no))
            conn.commit()
            cls.close_desired_db(conn, cursor)
        finally:
            ResponseHandler.lock.release()

    @classmethod
    def update_attachment_download_date_in_database(cls, tracing_no):
        try:
            ResponseHandler.lock.acquire(True)
            conn, cursor = cls.initialize_database()
            cursor.execute('''
                UPDATE processed_letters
                SET date_attachments_downloaded=?
                WHERE tracing_no=?
            ''', (datetime.datetime.now().replace(microsecond=0), tracing_no))
            conn.commit()
            cls.close_desired_db(conn, cursor)
        finally:
            ResponseHandler.lock.release()

params = {
    "Audited" : "true",
    "AuditorRef" : "-1",
    "Category" : "-1",
    "Childs" : "true",
    "CompanyState" : "-1",
    "CompanyType" : "-1",
    "Consolidatable" : "true",
    "IsNotAudited" : "false",
    "Length" : "-1",
    "LetterType" : "-1",
    "Mains" : "true",
    "NotAudited" : "true",
    "NotConsolidatable" : "true",
    "PageNumber" : "10",
    "Publisher" : "false",
    "TracingNo" : "-1",
    "search" : "false",
}


print(ResponseHandler.get_letter_by_tracing_no(1090245))

# Time stamp without millisecond
# data = ResponseHandler.get_letter_by_tracing_no(1090284)
# print(data[1])
# print(data[2])

#"https://search.codal.ir/api/search/v2/q"

# link , param = utils.split_url("https://codal.ir/Reports/Attachment.aspx?LetterSerial=UwtY%2b1IxgsD3YdSlR8szBQ%3d%3d")
# res = request.ApiRequest(link, param, "ATTACHMENT").send_requests()
# ResponseHandler(res).process_response()

# ResponseHandler.initialize_database()
