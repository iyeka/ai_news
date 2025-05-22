from typing import Iterable, Callable
import re
import config
import csv
import io

class BaseSave:
    def __init__(self, sheet_name):
        self.sheet = config.setup_google_sheets_api()
        self.sheet_id = config.SPREADSHEET_ID
        self.sheet_name = sheet_name

    def save_to_google_sheets(self, data):
        body = {
        'values': data
        }
        response = self.sheet.values().append(
            spreadsheetId=self.sheet_id,
            range=f"{self.sheet_name}!A2:Z",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()

        print(f"✅ New data appended successfully: {response.get('updates').get('updatedRange')}")

    def get_column_from_google_sheets(self, column_heading):
        result = (
            self.sheet
            .values()
            .get(
                spreadsheetId=self.sheet_id,
                range=f'{self.sheet_name}!{column_heading}2:{column_heading}',
                # get the hyperlink instead of the link title.
                valueRenderOption='FORMULA',
                )
            .execute()
        )
        column = result.get('values', ())
        return column

    def get_existing_data(self, column):
        existing_data_set = {''.join(row) for row in column}
        return existing_data_set

    def get_new_data(self, column_heading, data):
        letter_into_number = ord(column_heading) - ord("A")
        new_data_set = {row[letter_into_number] for row in data}
        return new_data_set
                 
class YoutubeSave(BaseSave):
    def get_base_url(self, url):
        # This regex grabs the main video URL without the timestamp
        match = re.search(r'v=([a-zA-Z0-9]+)', url)
        if match:
            return match.group(1)
        # fallback if regex doesn't match
        return url
    
    def get_existing_data(self, column):
        print("I'm calling youtube")
        existing_data_set = set()

        for row in column:
            string = ''.join(row)
            key_string = self.get_base_url(string) 
            existing_data_set.add(key_string)

        return existing_data_set
    
    def get_new_data(self, column_heading, data):
        print("I'm calling youtube")
        letter_into_number = ord(column_heading) - ord("A")
        new_data_set = set()

        for row in data:
            cell = row[letter_into_number]
            key_string = self.get_base_url(cell)
            new_data_set.add(key_string)

        return new_data_set
    
    def duplicated_or_save(self, data):
        column = self.get_column_from_google_sheets(config.YOUTUBE_SHEET_LINK_COLUMN)
        existing_data_set = self.get_existing_data(column)
        new_data_set = self.get_new_data(config.YOUTUBE_SHEET_LINK_COLUMN, data)
        if existing_data_set & new_data_set:
            print(f"Duplicate data found {data}, skipping...")
            return
        else:
            self.save_to_google_sheets(data)

def get_multiple_users_posts(keywords: Iterable, function:Callable):
    posts = []
    for keyword in keywords:
        posts.extend(function(keyword))
    return posts

def finalize_data(posts: list[dict]):
    memory = io.StringIO()
    writer = csv.DictWriter(memory, fieldnames=posts[0].keys())
    writer.writerows(posts)

    memory.seek(0) # cursor back to the first line.
    reader = csv.reader(memory)
    rows = [row for row in reader]

    return rows