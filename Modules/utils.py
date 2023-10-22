from urllib.parse import urlparse, parse_qs, urljoin, urlencode, unquote
from html.parser import HTMLParser
import os
import requests
import json
import hashlib


def Title_to_filename(Title : str) -> str:
    return Title.replace("/", "_")

def mime_to_extension(mime_type):
    mime_to_extension = {
        # Common Documents
        'application/msword': '.doc',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'application/vnd.ms-excel': '.xls',
        'application/ms-excel': '.xls',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
        'application/vnd.openxmlformats-officedocument.spre': '.xlsx',
        'application/pdf': '.pdf',
        'application/rtf': '.rtf',
        'text/plain': '.txt',

        # Archives
        'application/zip': '.zip',
        'application/x-tar': '.tar',
        'application/x-gzip': '.gz',
        'application/x-bzip2': '.bz2',
        'application/x-rar': '.rar',  # Added RAR format
        'application/x-7z': '.7z',
        'application/x-7z-compressed': '.7z',
        'application/x-rar-compressed': '.rar',  # Added RAR format

        # HTML
        'text/html': '.html',
        'application/xhtml+xml': '.xhtml',

        # JSON
        'application/json': '.json',

        # XML
        'application/xml': '.xml',
        'text/xml': '.xml',
        
        # Audio
        'audio/mpeg': '.mp3',
        'audio/wav': '.wav',
        'audio/x-ms-wma': '.wma',
        'audio/vnd.rn-realaudio': '.ra',

        # Images
        'image/jpeg': '.jpg',
        'image/png': '.png',
        'image/gif': '.gif',
        'image/tiff': '.tiff',
        'image/bmp': '.bmp',
        'image/svg+xml': '.svg',
        'image/x-icon': '.ico'
    }
    
    return mime_to_extension.get(mime_type, None)

def letter_handler(letter : dict[str, str | bool]) -> dict[str, str]:
    """_summary_

    Args:
        letter (dict[str, str | bool]): letter to be handled

    Returns:
        dict[str, str]: handled letter
    """
    letter_dict : dict[str, str] = {}
    for key, val in letter.items():
        if key in ['AttachmentUrl', 'PdfUrl', 'ExcelUrl', 'TracingNo', 'Title', 'CompanyName']:
            if key == 'AttachmentUrl' and val != '':
                letter_dict[key] = "https://codal.ir" + val
            elif  key == 'PdfUrl' and val != '':
                letter_dict[key] = "https://codal.ir/" + val
            else:
                letter_dict[key] = val
    return letter_dict

def attachments_files_handler(links : str) -> list[str]:
    return json.loads(links)

def generate_hash(file_name):
    sha256 = hashlib.sha256()
    sha256.update(file_name.encode('utf-8'))
    return sha256.hexdigest()

def path_validation(path : str) -> str:
    
    # get parent directory
    dir = os.path.dirname(path)
    
    os.makedirs(dir, exist_ok=True)
    
    if os.path.exists(path):
        for i in range(2, 100000):
            if not os.path.exists(path.split('.')[0] + f'_{i}.' + path.split('.')[1]):
                path = path.split('.')[0] + f'_{i}.' + path.split('.')[1]
                file_name = os.path.basename(path)
                if len(file_name.encode("utf-8")) > 255:
                    hashed_name = generate_hash(file_name)
                    path = os.path.join(dir, hashed_name + "." + path.split('.')[1])
                    with open(os.path.join(dir, "names.txt"), "a") as f:
                        f.write(f"{hashed_name} : {file_name}\n")
                    f.close()
                break
    else:
        file_name = os.path.basename(path)
        if len(file_name.encode("utf-8")) > 255:
            hashed_name = generate_hash(file_name)
            path = os.path.join(dir, hashed_name + "." + path.split('.')[1])
            with open(os.path.join(dir, "names.txt"), "a") as f:
                f.write(f"{hashed_name} : {file_name}\n")
            f.close()
        
    return path


class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.onclick_attributes = []

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            for attr, value in attrs:
                if attr == 'onclick':
                    url = value.split("'")[1]
                    self.onclick_attributes.append(url)


def construct_url(base_url, params):
    url = urljoin(base_url, urlencode(params))
    url = unquote(url, encoding='utf-8')
    return url

def split_url(url):
    parsed_url = urlparse(url)

    # Extract base URL
    base_url = parsed_url.scheme + '://' + parsed_url.netloc + parsed_url.path

    # Parse query parameters and encode them in UTF-8
    query_params = parse_qs(parsed_url.query, encoding='utf-8')
    for key, val in query_params.items():
        query_params[key] = val[0]

    return base_url, query_params

def split_list(input_list : list, n : int) -> list[list]:
    """_summary_

    Args:
        input_list (list): list to be splitted
        n (int): number of chunks

    Returns:
        list[list]: splitted list
    """
    return [input_list[i * n:(i + 1) * n] for i in range((len(input_list) + n - 1) // n )]

def path_finder(response : requests.models.Response , Title : str, CompanyName : str, type : str) -> str:
    ext = mime_to_extension(response.headers['Content-Type'])
    if ext == None :
        ext = "." + response.headers['Content-Type'].split(";")[0].split("/")[1]
    if type == "ATTACHMENTS":
        path = os.path.join(os.getenv("PATH").split(':')[0], CompanyName, "Attachments", Title_to_filename(Title) + ext)
    else:
        path = os.path.join(os.getenv("PATH").split(':')[0], CompanyName, "Letters", Title_to_filename(Title) + ext)
    
    return path_validation(path)



