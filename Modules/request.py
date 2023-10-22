import requests
import time
import os
from db_manager import DBManager

# Define constants for limiting and retries
MAX_RETRIES = int(os.getenv("MAX_RETRIES"))
BACKOFF_FACTOR = float(os.getenv("BACKOFF_FACTOR"))
MAX_WORKERS = int(os.getenv("MAX_WORKERS"))
DESIRED_CHUCKS = int(os.getenv("DESIRED_CHUCKS"))
DB_PATH = os.getenv("DB_PATH")

class ApiRequest:
    ses = requests.Session()
    ses.keep_alive = True
    
    headers = {
        "JSON": {
            'Host': 'search.codal.ir',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:114.0) Gecko/20100101 Firefox/114.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://codal.ir',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://codal.ir/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site'
        },
        "DOWNLOAD": {
            'Host': 'codal.ir',
            'Connection': 'keep-alive',
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Referer': 'https://codal.ir/ReportList.aspx?search',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Cookie': 'usrInfo=uInfo=4kfUlsUv2vhhgWYgRaWSZmv8g9Oqt8D3GFcyV5iWgmPVLTxjRS69j7+YB4wxbbtOcWDkqX2oTdZ+AVyQQQaQQQQ03e2iBaBfQQQaQQQUlh284oOXrETFREdLDy+J3ibsUjZuBfAKWVOu; ASP.NET_SessionId=gxomzltxoozmvcb1m4oquyv2; Unknown=287641772.20480.0000; TS0169f355=01f9930bd260cadadfdfb389ca0bebbf285c6d8b62fd70be0905ce5219962e74b900781e472f415404317128e5c6b8e970ce7d4e6910252a6571a8fd291582967b941792f2060c94ab8ceb16858dc769a923cd0173'
        },
        'ATTACHMENT' : {
            'Host': 'codal.ir',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:114.0) Gecko/20100101 Firefox/114.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
            'Connection': 'keep-alive',
            'Cookie': 'ASP.NET_SessionId=ajelzaxckjbyfchbc3flnido; usrInfo=uInfo=+Dr3mR7dMgE6YzVLOh2dw1gkuopL7GuvItSR4+q3cbXpDAly4E0XunUdwKatOl5ef+Iuwa6llXIeXXN+k9TorWcXZhwAtOCAvw04HnwaQ4SNQH5U9yVltexZ+KyolFSs; Unknown=103092396.20480.0000; TS0169f355=01f9930bd2dab42a0b8ea80de6747d763c3d16d52db0eefdbc0ddb797c8c67a5cc982a8ab2574d1ecc069702615033a238bc3feacc7b1257f79619cfa7d0bd1048d5b732975f6162561c421b4b8855ad1bea1fbc22; TS0154d277=01f9930bd2581a3b2f84959e9cff8afa7c6f31791212d6fdfd116a27107d2122d45a2c12e59a52fc9036c04879974a700f27d97ba62828f226e4886568100a29521b74f1ff; ScreenWidth1=1850; ScreenHeight1=968',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        }
    }
    
    failed_responses : list[dict[str, str | dict[str, str]]] = []
    
    def __init__(self, url, query_params, headers):
        """
        Args:
            url (str): URL to send request to
            query_params (dict): Query parameters to send with request
            headers (dict): Headers to send with request
        """
        self.url = url
        self.query_params = query_params
        self.headers = ApiRequest.headers[headers]
        
    def send_requests(self):
        """
        Send request to the url with query params and headers
        Returns:
            [type]: response | None
        """
        retries = 0
        while retries < MAX_RETRIES:
            try:
                response = ApiRequest.ses.get(self.url, params=self.query_params, headers=self.headers)
                if response.status_code == 200:
                    return response
                else:
                    retries += 1
                    time.sleep(BACKOFF_FACTOR * (2 ** retries))
            except Exception as e:
                print(e)
                retries += 1
                time.sleep(BACKOFF_FACTOR * (2 ** retries))
        print(f"Failed to get response from {self.url} with query params {self.query_params} after {MAX_RETRIES} retries")
        DBManager(DB_PATH).add_failed_request(self.url, self.query_params, self.headers)
        
    @classmethod
    def get_session_cookies(cls):
        return cls.ses.cookies.get_dict()

    @classmethod
    def set_session_cookies(cls):
        cls.ses.cookies.update({"Cookie" : "ASP.NET_SessionId=25cff4hnyk14js0r3vt4wfne; usrInfo=uInfo=JwNos4Ji7iRrtYkYey0k3+rynNZ1zBPqwTlYvdVcGUrNjTxLrLPQQQaQQQcNBQQQaQQQ0FuvCstaQQQaQQQW8JQQQaQQQhjqGqGivzLiWGoEnzwQOvjCYSInQQQaQQQoYaSxnY+hwsS5tlZW5GNy2YrWAZ9ksu; Unknown=287641772.20480.0000; TS0169f355=01f9930bd2cbbd20d1a5376c5bdf8c4685d134cc555e6fab661cbe0459ed6eaef85894e75f6ce988d41e8e50e1ce8642652f8e066975e13bcd1962e740eabf611352a7a54b09bc3319ee91e68fc5f6a354890250ad; TS0154d277=01f9930bd29e2fc015a1bc6ba14f0f24d998f82d3168dabda39e69db0a512ae473eec3dfc473b6d0960a692a322840472a7f3bf751756e028bff4f516edf48e50fb1c0ec43; ScreenWidth1=1850; ScreenHeight1=968"})
