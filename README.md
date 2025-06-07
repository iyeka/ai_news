# AI News Scrapper

## Goal

- Scrape AI News from Youtube.
- Scrape usecases of AI for monetization from communities.
- Put the result in Google Sheets.

## Directory Tree

```text
📁 project_root/
├── main.ipynb                          ← The script that runs everything
├── .env                                ← Private variables
├── requirements.txt                    ← Python dependencies
│
├── config/                             ← Folder for YouTube-related code
│   ├── __init__.py
│   ├── config.py                       ← Configuration for API and sheet settings
│
├── communities/
│   ├── youtube.py
│   │   ├── def fetch_data
│   │   ├── def AI_summarization
│   ├── x.py                            ← get posts by username
│   ├── reddit.py                       ← hot posts from subreddits
│   ├── threads.py                      ← timeline posts
│   ├── geeknews.py                     ← https://news.hada.io/
│
├── utils/                              ← Shared utilities
│   ├── save.py
│   │   ├── def save_to_google_sheets
│   │   ├── def showing_on_streamlit    ← It can be replaced with Nicegui
│   ├── modify_data.py
│
```
