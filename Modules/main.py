import jobs
import os
import utils
import json
import requests
from persian_typer import type_persian

def print_company_list(company_list, selected_indices=set(), page=1):
    def print_item(index, company_name, selected, max_length):
        checkbox = "[X]" if selected else "[ ]"
        print(f"{index+1:<4d}. {checkbox} {type_persian(company_name)}", end="")
        print(" " * ((max_length - len(company_name)) - 10), end="")

    max_length = max(len(company) for company in company_list)
    num_columns = 3
    column_width = max_length + 8  # 4 for index, 4 for checkbox

    num_items = len(company_list)
    items_per_page = (num_items + 2) // 3 if page == 1 else (num_items + 2) // 3 if page == 2 else num_items - (2 * ((num_items + 2) // 3))

    start_index = (page - 1) * items_per_page
    end_index = min(start_index + items_per_page, num_items) if page < 3 else num_items

    for i in range(start_index, end_index):
        selected = i in selected_indices
        print_item(i, company_list[i], selected, max_length)

        if (i + 1 - start_index) % num_columns == 0:
            print()

    print("\n\nOptions:")
    print("a. Select All")
    print("d. Deselect All")
    print("q. Previous Page")
    print("e. Next Page")
    print("\nPress Enter to finish")

    return selected_indices

def get_companies() -> list[tuple[int, str]]:
    headers = {
        'Host':             'search.codal.ir',
        'User-Agent':       'Mozilla/5.0 (Windows NT 10.0; rv:114.0) Gecko/20100101 Firefox/114.0',
        'Accept':           'application/json, text/plain, */*',
        'Accept-Language':  'en-US,en;q=0.5',
        'Accept-Encoding':  'gzip, deflate, br',
        'Origin':           'https://codal.ir',
        'DNT':              '1',
        'Connection':       'keep-alive',
        'Referer':          'https://codal.ir/',
        'Sec-Fetch-Dest':   'empty',
        'Sec-Fetch-Mode':   'cors',
        'Sec-Fetch-Site':   'same-site',
    }
    url, query_params = utils.split_url('https://search.codal.ir/api/search/v1/companies')
    response = requests.get(url, params=query_params, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Failed to get companies with status code {response.status_code}")
    
    companies = []
    for company in json.loads(response.text):
        companies.append((company['i'], company['sy']))
    return companies

def menu(companies) -> set[int]:
    selected_indices = set()

    page = 1
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"Page {page}\n")
        selected_indices = print_company_list(companies, selected_indices, page)

        user_input = input("Enter your choice (a/d/q/e/Enter): ").lower()

        
        # Handle list input
        if "-" in user_input:
            raw = user_input.strip()
            str_indx, end_indx = [int(i) for i in raw.split("-")]
            for indx in range(str_indx, end_indx + 1):
                ind = indx - 1
                if 0 <= ind < len(companies):
                    if ind in selected_indices:
                        selected_indices.remove(ind)
                    else:
                        selected_indices.add(ind)
                else:
                    print("Invalid index!")
        
        # Handle digit input
        if user_input.isdigit():
            index = int(user_input) - 1
            if 0 <= index < len(companies):
                if index in selected_indices:
                    selected_indices.remove(index)
                else:
                    selected_indices.add(index)
            else:
                print("Invalid index!")

        # Handle options input
        if user_input == 'a':
            selected_indices = set(range(len(companies)))  # Select all
        elif user_input == 'd':
            selected_indices = set()  # Deselect all
        elif user_input == 'q' and page > 1:
            page -= 1  # Go back one page
        elif user_input == 'e' and page < 3:
            page += 1  # Go forward one page
        elif user_input == '':
            break  # User pressed Enter, finish the process

    print("\nSelected Companies:")
    for i, company in enumerate(companies):
        if i in selected_indices:
            print(f"{i+1}. [X] {type_persian(company)}")
    print(f"\nTotal Selected Company : {len(companies)}")
    return selected_indices


if __name__ == "__main__":
    companies = get_companies()
    selected_indices = list(menu(companies = [company[1] for company in companies]))
    selected_companies = [companies[i] for i in selected_indices]
    print([(i, type_persian(j)) for i,j in selected_companies])
    jobs.companies_batch_handler(selected_companies)
    jobs.get_attachments()
    jobs.download_pdf()
    jobs.download_attachments_files()