from typing import Iterable, Callable, Optional
import config
import csv
import io

class BaseSave:
    def __init__(self, sheet_name):
        self.sheet = config.setup_google_sheets_api()
        self.sheet_id = config.SPREADSHEET_ID
        self.sheet_name = sheet_name

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
        
    def get_existing_data_set(self, column_header="Link", fn_get_base_url: Optional[Callable] = None):
        existing_data = self.get_data_from_google_sheets()
        header = existing_data[0]
        rows = existing_data[1:]
        header_index = header.index(column_header)
        existing_data_set = set()
        for row in rows:
            indexed_row = row[header_index]
            base_url = fn_get_base_url(indexed_row) if fn_get_base_url else indexed_row
            existing_data_set.add(base_url)
        return existing_data_set
    
    def duplicated_check(self, new_data:list[dict], fn_get_base_url: Optional[Callable] = None):
        data = []
        existing_data_set = self.get_existing_data_set(fn_get_base_url=fn_get_base_url)
        for post in new_data:
            url = post.get('link')
            base_url = fn_get_base_url(url)
            if base_url in existing_data_set:
                print(f"Duplicate data found {url}, skipping...")
            else:
                data.append(post)
        return data

    def duplicated_or_save(self, keywords: Iterable, fn_get_posts: Callable, fn_get_base_url: Optional[Callable] = None):
        posts = fn_get_posts(keywords)
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