# %%
from youtube_transcript_api import YouTubeTranscriptApi

def get_youtube_transcript(video_id):
        try:
                transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
                first_transcript = transcripts.find_transcript([t.language_code for t in transcripts])
                transcript = first_transcript.fetch().to_raw_data()
                return transcript
        
        except Exception as e:
                print(f"⚠️ Error: {e}")

# %%
from yt_dlp import YoutubeDL

class YouTubeInfoExtractor:
    def __init__(self, url):
        self.url = url
        self.info = self._fetch_info()

    def _fetch_info(self):
        ydl_opts = {'skip_download': True}
        with YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(self.url, download=False)

    def get_title(self):
        return self.info.get('title')

    def get_chapters(self):
        return self.info.get('chapters')

    def get_upload_date(self):
        return self.info.get('upload_date')

# %%
def group_transcript_by_chapters(transcript, chapters):

    chapters_transcript = []

    for chapter in chapters:
        chapter_transcript = [
            t["text"]
            for t in transcript
            if chapter["start_time"] <= t["start"] < chapter["end_time"]
            ]
        
        chapters_transcript.append({
            chapter['title']: ' '.join(chapter_transcript)
        })

    return chapters_transcript

# %%
from dotenv import load_dotenv
import os
from openai import OpenAI

# Load variables from .env into environment
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("OPENAI_MODEL_NAME")

# Create OpenAI client
client = OpenAI(api_key=api_key)

def summarize(dictionary):
    response = client.chat.completions.create(
        model = model,
        messages = [
            {"role": "system", "content": "You are a helpful assistant that summarizes text and makes the output into CSV format without any extra text."},
            
            {"role": "user", "content": 
                f"""You'll create a csv row with 4 cells using dictionary name {dictionary} you'll receive.
                
                Dictionary has:
                    - Key = Title (DO NOT summarize or change it. Use it as-is.)
                    - Value = Content about the key (you need to summarize and divide into fields).

                Expected Output:
                    1. have 4 cells:
                        - DICTIONARY KEY
                        - Descriptions about the key.
                        - Features related to the key.
                        - Specific usage examples.

                    2. No extra text or explanation. Output only has CSV format.
                    3. Separate each cell with | instead of comma.

                Example output:
                엔비디아, 모든 소리 생성 가능한 AI 공개|음악부터 효과음까지 모든 소리를 생성|사운드와 스피치와 뮤직이 통합된 모델|효과음을 음악으로 변환, 음악에서 보컬 분리, 텍스트로 소리 생성 및 변환
                """},
            ],
                temperature=0.5,
                max_tokens=300,
    )
    return response.choices[0].message.content.strip()

# %%
def finalize_csv_text(date, transcript, url, chapters, title):
    csv_text = []
    
    for chapter, dictionary in zip(chapters, transcript):
        ai_summary = summarize(dictionary)
        row = ai_summary.split("|")

        # Add date as the first cell
        row.insert(0, date)

        # Create the timestamped link for the current chapter
        link = f'=HYPERLINK("{url}&t={int(chapter["start_time"])}", "{title}")'
        row.append(link)

        # Add the full row to the CSV list
        csv_text.append(row)

    return csv_text

# %%
import re

def get_base_url(url):
    # This regex grabs the main video URL without the timestamp
    match = re.match(r"(https:\/\/www\.youtube\.com\/watch\?v=[^&]+)", url)
    if match:
        return match.group(0)
    # fallback if regex doesn't match
    return url

# %%
from googleapiclient.discovery import build
from google.oauth2 import service_account

# --------- Setup Google Sheets API ---------
creds = service_account.Credentials.from_service_account_file(
'credentials.json',
scopes=['https://www.googleapis.com/auth/spreadsheets']
)

service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

# --------- Define your Spreadsheet ---------
SPREADSHEET_ID = '1qr_CluX6H4sUEfHwbntpRhj4kj2ldTaCENN00IT-8rg'
SHEET_NAME = 'AI_News'

def save_to_google_sheet(csv_text, new_link):
    seen = set()

    # 1. Read all existing rows to check duplication
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                            range=f"{SHEET_NAME}!F2:F").execute()
    existing_rows = result.get('values', [])

    for row in existing_rows:
        if row:
            seen_link = get_base_url(row[-1])  # last column = link
            seen.add(seen_link)

    if new_link in seen:
        print(f"Duplicate link found ({new_link}), skipping...")
        return
    # 2. Append the new data
    else:
        body = {
        'values': csv_text
    }
        response = sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A2:Z",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()

        print(f"✅ New data appended successfully: {response.get('updates').get('updatedRange')}")

# %%
def main(video_id):
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    full_transcript = get_youtube_transcript(video_id)

    info = YouTubeInfoExtractor(video_url)
    title, chapters, date = info.get_title(), info.get_chapters(), info.get_upload_date()

    chapters_transcript = group_transcript_by_chapters(transcript=full_transcript, chapters=chapters)

    csv_text = finalize_csv_text(date=date, transcript=chapters_transcript, url=video_url, chapters=chapters, title=title)

    save_to_google_sheet(csv_text=csv_text, new_link=video_url)