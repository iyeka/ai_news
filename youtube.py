from youtube_transcript_api import YouTubeTranscriptApi
from yt_dlp import YoutubeDL
import re
import config
import utils

def get_youtube_transcript(video_id):
    transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
    first_transcript = transcripts.find_transcript([t.language_code for t in transcripts])
    transcript = first_transcript.fetch()
    return transcript

def get_youtube_info(url):
    ydl_opts = {'skip_download': True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        info_dict = dict(
            title = info.get('title'),
            chapters = info.get('chapters'),
            upload_date = info.get('upload_date'),
        )
    return info_dict

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

def summarize(dictionary):
    client = config.get_client()
    response = client.chat.completions.create(
        model = config.OPENAI_MODEL_NAME,
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
        temperature=0.4,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()

def finalize_data(date, transcript, url, title, chapters):
    data = []
    
    # dictionary for AI summarization, and chapter for time in the link.
    for chapter, dictionary in zip(chapters, transcript):
        ai_summary = summarize(dictionary)
        # making a string into a list.
        row = ai_summary.split("|")

        # Add date as the first cell
        row.insert(0, date)

        # Create the timestamped link for each chapter
        link = f'=HYPERLINK("{url}&t={int(chapter["start_time"])}", "{title}")'
        row.append(link)

        # Add the full row to the CSV list
        data.append(row)

    return data

''' save to csv instead of google sheets
import os
import csv

def save_to_csv(csv_text, new_link, filename="AI_News.csv"):
    # check if file existed
    file_exists = os.path.exists(filename)

    seen = set()

    # check duplication
    if file_exists:
        with open(filename, "r", encoding="utf-8-sig") as file:
            reader = csv.reader(file)
            # Skip the header and get the next row. if it doesn't exist, return None.
            next(reader, None)

            for row in reader:
                if row:
                    seen_link = get_base_url(row[-1])
                    seen.add(seen_link)

    if new_link in seen:
        print(f"Duplicate link found ({new_link}), skipping...")
        return

    else:
        # 'a' mode for append, 'w' mode for write if new file
        with open(filename, "a", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)

            # If the file does not exist yet, write header first
            if not file_exists:
                writer.writerow(["Upload Date", "Title", "Description", "Features", "Usage Examples", "Link"])
            writer.writerows(csv_text)
'''

def get_base_url(url):
    # This regex grabs the main video URL without the timestamp
    match = re.search(r'v=([a-zA-Z0-9]+)', url)
    if match:
        return match.group(1)
    # fallback if regex doesn't match
    return url

def main(video_id):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    cl_basesave = utils.BaseSave(config.YOUTUBE_SHEET)

    existing_data_set = cl_basesave.get_existing_data_set(fn_get_base_url=get_base_url)
    if video_id in existing_data_set:
        print(f"Duplicate link found {video_url}, skipping...")
        return

    info = get_youtube_info(video_url)
    title, chapters, date = info.get('title'), info.get('chapters'), info.get('upload_date')
    if not chapters:
        print("Sorry, There's no chapter in the Youtube video.")
        return
    
    try:
        full_transcript = get_youtube_transcript(video_id)
    except TypeError as e:
        print(f"An error occurred while fetching the transcript: {e}")
    else:
        if not full_transcript:
            print("Sorry, There's no transcript in the Youtube video.")
            return
        
    chapters_transcript = group_transcript_by_chapters(transcript=full_transcript, chapters=chapters)

    data = finalize_data(date=date, transcript=chapters_transcript, url=video_url, title=title, chapters=chapters)

    cl_basesave.save_to_google_sheets(data)