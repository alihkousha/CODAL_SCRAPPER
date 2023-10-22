import request
import response_manager
import utils
import json
import os
from db_manager import DBManager
from concurrent.futures import ThreadPoolExecutor
import time
from persian_typer import type_persian

# Define constants for limiting and retries
MAX_WORKERS = int(os.getenv("MAX_WORKERS"))
DESIRED_CHUCKS = int(os.getenv("DESIRED_CHUCKS"))
PATH = os.getenv("PATH").split(':')[0]
DB_PATH = os.getenv("DB_PATH")

# _________Page's Jobs Handling__________

def get_pages() -> str:
    param = {
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
        "PageNumber" : "1",
        "Publisher" : "false",
        "TracingNo" : "-1",
        "search" : "false",
    }
    res = request.ApiRequest("https://search.codal.ir/api/search/v2/q", param, "JSON").send_requests()
    return json.loads(res.content)['Page']


def get_letters(tracingNO : str = '') -> None:
        
    pages = get_pages()
    params = []
    for page in range(1, int(pages) + 1):
        params.append({
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
            "PageNumber" : page,
            "Publisher" : "false",
            "TracingNo" : "-1",
            "search" : "false",
            }
        )
    
    params_list = utils.split_list(params, DESIRED_CHUCKS)
    
    with ThreadPoolExecutor(max_workers = MAX_WORKERS) as executor:
        for params in params_list:
            executor.submit(handle_batch_pages, params, tracingNO)


def handle_batch_pages(params : list[dict[str, str]], tracingNO : str = '') -> None:
    
    if "Symbol" in params[0]:
        company_name = params[0]['Symbol']

    if company_name:
        print(f"Start processing pages from {params[0]['PageNumber']} to {params[-1]['PageNumber']} of {type_persian(company_name)}")
    else:
        print(f"Start processing pages from {params[0]['PageNumber']} to {params[-1]['PageNumber']}")

    with ThreadPoolExecutor(max_workers = MAX_WORKERS) as executor:
        for param in params:
            if company_name:
                executor.submit(handle_page, param, tracingNO, company_name)
            else:
                executor.submit(handle_page, param, tracingNO)
    if company_name:
        print(f"Finished processing pages from {params[0]['PageNumber']} to {params[-1]['PageNumber']} of {type_persian(company_name)}")
    else:
        print(f"Finished processing pages from {params[0]['PageNumber']} to {params[-1]['PageNumber']}")
    # print(response_manager.ResponseHandler.get_processed_letters())
    # print([next(i) for i in response_manager.ResponseHandler.get_processed_letters()])


def handle_page(param : int, tracingNO : str = '', company_name : str = '') -> None:
    print(f"Start processing page : {param['PageNumber']} of {type_persian(company_name)}" if company_name != '' else f"Start processing page : {param['PageNumber']}")
    try:
        res = request.ApiRequest("https://search.codal.ir/api/search/v2/q", param, "JSON").send_requests()
        response_manager.ResponseHandler(res).process_response(tracingNO)
    except Exception as e:
        print(f"Error while processing page {param['PageNumber']} of {company_name}: {e}" if company_name != '' else f"Error while processing page {param['PageNumber']} : {e}")
        return
    print(f"Successfully processed page : {param['PageNumber']} of {type_persian(company_name)}" if company_name != '' else f"Successfully processed page : {param['PageNumber']}")


# _________Get Letters by Company Symbol__________

def get_company_total_pages(query_params : dict[str | str]) -> int:
    res = request.ApiRequest("https://search.codal.ir/api/search/v2/q", query_params, "JSON").send_requests()
    return json.loads(res.content)['Page']

def get_company_letters(company_symbol : str, Isic : int) -> list[dict[str, str]] | None:
    
    if Isic != '':
        query_params = {
            "Audited": "true",
            "AuditorRef": "-1",
            "Category": "-1",
            "Childs": "true",
            "CompanyState": "-1",
            "CompanyType": "-1",
            "Consolidatable": "true",
            "IsNotAudited": "false",
            "Isic": f"{Isic}",
            "Length": "-1",
            "LetterType": "-1",
            "Mains": "true",
            "NotAudited": "true",
            "NotConsolidatable": "true",
            "PageNumber": "1",
            "Publisher": "false",
            "Symbol": company_symbol,
            "TracingNo": "-1",
            "search": "true"
        }
    else:
        query_params = {
            "Audited": "true",
            "AuditorRef": "-1",
            "Category": "-1",
            "Childs": "true",
            "CompanyState": "-1",
            "CompanyType": "-1",
            "Consolidatable": "true",
            "IsNotAudited": "false",
            "Length": "-1",
            "LetterType": "-1",
            "Mains": "true",
            "NotAudited": "true",
            "NotConsolidatable": "true",
            "PageNumber": "1",
            "Publisher": "false",
            "Symbol": company_symbol,
            "TracingNo": "-1",
            "search": "true"
        }
        
    pages = get_company_total_pages(query_params)
    
    if int(pages) == 0:
        return
    
    params = []
    for page in range(1, pages + 1):
        if Isic != '':
            params.append({
                "Audited": "true",
                "AuditorRef": "-1",
                "Category": "-1",
                "Childs": "true",
                "CompanyState": "-1",
                "CompanyType": "-1",
                "Consolidatable": "true",
                "IsNotAudited": "false",
                "Isic": f"{Isic}",
                "Length": "-1",
                "LetterType": "-1",
                "Mains": "true",
                "NotAudited": "true",
                "NotConsolidatable": "true",
                "PageNumber": page,
                "Publisher": "false",
                "Symbol": company_symbol,
                "TracingNo": "-1",
                "search": "true"
            })
        else:
            params.append({
                "Audited": "true",
                "AuditorRef": "-1",
                "Category": "-1",
                "Childs": "true",
                "CompanyState": "-1",
                "CompanyType": "-1",
                "Consolidatable": "true",
                "IsNotAudited": "false",
                "Length": "-1",
                "LetterType": "-1",
                "Mains": "true",
                "NotAudited": "true",
                "NotConsolidatable": "true",
                "PageNumber": page,
                "Publisher": "false",
                "Symbol": company_symbol,
                "TracingNo": "-1",
                "search": "true"
            })
            
    return params

def get_company_letters_by_symbol(company_symbol : str, Isic : int) -> None:
    params = get_company_letters(company_symbol, Isic)
    if params == None:
        return
    
    params_list = utils.split_list(params, DESIRED_CHUCKS)
    
    with ThreadPoolExecutor(max_workers = MAX_WORKERS) as executor:
        for params in params_list:
            executor.submit(handle_batch_pages, params)

def companies_job_handler(companies : list[tuple[int, str]]) -> None:
    
    with ThreadPoolExecutor(max_workers = MAX_WORKERS) as executor:
        for company in companies:
            executor.submit(get_company_letters_by_symbol, company[1], company[0])

def companies_batch_handler(companies : list[tuple[int, str]]) -> None:
    companies_list = utils.split_list(companies, DESIRED_CHUCKS)
    
    with ThreadPoolExecutor(max_workers = MAX_WORKERS) as executor:
        for companies in companies_list:
            executor.submit(companies_job_handler, companies)

# _________Attachment's Jobs Handling__________


def get_attachments():
    attachments = response_manager.ResponseHandler.get_attachments_from_database()

    if not attachments:
        print("No new attachments to process.")
        return
    
    # raise Exception()
    attachments_list = utils.split_list(attachments, DESIRED_CHUCKS)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executer:
        features = [executer.submit(handle_batch_attachments, links) for links in attachments_list]

    del features

def handle_batch_attachments(links : list[tuple[int, str]]) -> None:
    with ThreadPoolExecutor(max_workers = MAX_WORKERS) as executor:
        features = [executor.submit(handle_attachments, url, tracingNO) for tracingNO, url in links]
    # print(response_manager.ResponseHandler.processed_attachments)
    del features

def handle_attachments(url : str, tracingNO : int) -> None:
    print(f"Start processing attachments with tracingNO : {tracingNO}")
    try:
        if url != '' :
            link , param = utils.split_url(url)
            res = request.ApiRequest(link, param, "ATTACHMENT").send_requests()
            response_manager.ResponseHandler(res).process_response(str(tracingNO))
    except Exception as e:
        print(f"Error while processing attachments with tracingNO {tracingNO} : {e}")
        return
    print(f"Successfully processed attachments with tracingNO : {tracingNO}")


# _________File's Downloading___________

def download_pdf():
    links = response_manager.ResponseHandler.get_pdf_from_database()

    if not links:
        print("No new pdf to download.")
        return

    pdf_list = utils.split_list(links, DESIRED_CHUCKS)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executer:
        features = [executer.submit(handle_batch_files, links, 'PDF') for links in pdf_list]

    del features

def download_attachments_files():
    links = response_manager.ResponseHandler.get_attachments_files_from_database()
    
    if not links:
        print("No new attachments files to download.")
        return
    
    for i in range(len(links)):
        if links[i][1] != None:
            links[i] = (links[i][0], json.loads(links[i][1]))
        else:
            links[i] = (links[i][0], [])
    attachments_list = utils.split_list(links, DESIRED_CHUCKS)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executer:
        features = [executer.submit(handle_batch_files, links, 'ATTACHMENTS') for links in attachments_list]

    del features

def handle_batch_files(links : list[tuple[int, str]], type : str) -> None:
    if type in ['PDF', 'EXCEL']:
        with ThreadPoolExecutor(max_workers = MAX_WORKERS) as executor:
            features = [executor.submit(handle_download, TracingNO, [url], 'PDF') for TracingNO, url in links]
        del features
    else:
        with ThreadPoolExecutor(max_workers = MAX_WORKERS) as executor:
            features = [executor.submit(handle_download, TracingNO, urls, 'ATTACHMENTS') for TracingNO, urls in links]
        del features

def handle_download(TracingNO, Urls, type : str) -> None:
    with ThreadPoolExecutor(max_workers = MAX_WORKERS) as executor:
        features = [executor.submit(downloader, TracingNO, url, type) for url in Urls]

def downloader(TracingNO, Url, type : str):
    print(f"Start downloading file with tracingNO : {TracingNO}")
    if Url != '' or Url == None:
        try:
            link, par = utils.split_url(Url)
            res = request.ApiRequest(link, par, "DOWNLOAD").send_requests()
            response_manager.ResponseHandler(res).process_response(TracingNO, type)
            if type == 'PDF':
                response_manager.ResponseHandler.update_letter_download_date_in_database(TracingNO)
            elif type == 'ATTACHMENTS':
                response_manager.ResponseHandler.update_attachment_download_date_in_database(TracingNO)
        except Exception as e:
            print(f"Error while downloading file with tracingNO {TracingNO} : {e}")
            DBManager(DB_PATH).add_failed_download(TracingNO, Url)
            return
    else:
        print(f"File with tracingNO {TracingNO} has no link")
        return

def run_program_demon():
    print("Starting demon process")
    while True:
        try:
            get_letters()
            get_attachments()
            download_pdf()
            download_attachments_files()
        except Exception as e:
            print(f"Error in demon process: {e}")

        print("Finished processing all jobs. Going to sleep for 1 hour")
        # Sleep for a specified interval (e.g., 1 hour) before checking for new records again
        time.sleep(3600)

## TO-DO:
    # 1. Add Error Handler to each Job Done
    # 2. Add Logging to each Job  Done
    # 3. Add Tests to each Job
    # 4. Add save to file functionality to each class variable Done
    # 5. Create Date Created column in processed_letters table to start update logic
    # 6. Add update logic
    # 7. Add Date Downloaded column in processed_letters table to handle failed downloads
    # 8. mimic idm as download manager in python




# get_letters()
# get_attachments()
# download_pdf()
# download_attachments_files()

# companies = [('571906', 'وقوام'), ('343013', 'خمحرکه')]
# companies_batch_handler(companies)