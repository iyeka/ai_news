from typing import Iterable, Callable, Optional
import inspect
import logging
import config
import csv
import io

config.setup_logger()

class BaseSave:
    def __init__(self, sheet_name):
        self.sheet = config.setup_google_sheets_api()
        self.sheet_id = config.SPREADSHEET_ID
        self.sheet_name = sheet_name
        logging.debug(f"Google Sheets API is setup with {self.sheet_name}")

    def save_to_google_sheets(self, new_data:list[dict]):
        body = {
        'values': new_data
        }
        response = self.sheet.values().append(
            spreadsheetId=self.sheet_id,
            range=f"{self.sheet_name}!A2:Z",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()

        print(f"✅ New data appended successfully: {response.get('updates').get('updatedRange')}")

    def get_data_from_google_sheets(self):
        result = (
            self.sheet
            .values()
            .get(
                spreadsheetId=self.sheet_id,
                range=f'{self.sheet_name}!A:Z',
                # get the hyperlink instead of the link title.
                valueRenderOption='FORMULA',
                )
            .execute()
        )
        existing_data = result.get('values', ())
        return existing_data
        
    def get_rows_by_column_header(self, column_header="Link") -> list:
        existing_data = self.get_data_from_google_sheets()
        header = existing_data[0]
        rows = existing_data[1:]
        header_index = header.index(column_header)
        return [row[header_index] for row in rows]
    
    def duplicated_check(self, new_data:list[dict], fn_get_base_url: Optional[Callable]):
        data = []
        existing_data = self.get_rows_by_column_header()
        logging.debug(f"fetching {len(existing_data)} existing rows.")
        existing_data_set = set()
        for link in existing_data:
            base_url = fn_get_base_url(link)
            logging.debug(f"{base_url} is extracted from {link}.")
            existing_data_set.add(base_url)

        for post in new_data:
            link = post.get('link')
            logging.debug(f"Link key value '{link}' is found from the new_data.")
            base_url = fn_get_base_url(link)
            logging.debug(f"{base_url} is extracted from the the link.")
            if base_url in existing_data_set:
                print(f"Duplicate data found {link}, skipping...")
            else:
                data.append(post)
        return data

    async def duplicated_or_save(self, keywords: Iterable, fn_get_posts: Callable, fn_get_base_url: Optional[Callable]):
        get_posts = fn_get_posts(keywords)
        
        if inspect.iscoroutine(get_posts):
            posts = await get_posts
        else:
            posts = get_posts
        
        unduplicated_posts = self.duplicated_check(new_data=posts, fn_get_base_url=fn_get_base_url)

        if not unduplicated_posts:
            print("There are no datas to update.")
            return
        
        data = gsheets_format(unduplicated_posts)
        self.save_to_google_sheets(data)

def gsheets_format(posts: list[dict]):
    memory = io.StringIO()
    writer = csv.DictWriter(memory, fieldnames=posts[0].keys())
    writer.writerows(posts)

    memory.seek(0) # cursor back to the first line.
    reader = csv.reader(memory)
    rows = [row for row in reader]

    return rows