# AI News Scrapper

## Goal

- Scrape AI News from Youtube.
- Scrape usecases of AI for monetization from communities.
- Put the result in Google Sheets.

## Directory Tree

```text
📁 project_root/
├── main.py                     ← The script that runs everything
├── .env                        ← Configuration for API keys, sheet IDs, etc.
├── requirements.txt            ← Python dependencies
│
├── youtube/                    ← Folder for YouTube-related code
│   ├── __init__.py
│   ├── youtube_to_google_sheets.py
│   │   ├── def get_script
│   │   ├── def get_chapters
│   │   ├── def group_transcript_by_chapters
│   │   ├── def summarize as csv row
│   │   ├── def merge csv text
│   │   ├── def save to google sheet with duplication check
│
├── crewai_agent/               ← Folder for CrewAI-related code
│   ├── __init__.py
│   ├── search_channels.py      ← Search for useful X and Discord channels based on my recommendation.
│   ├── curate.py               ← curate useful posts
│
├── communities/
│   ├── __init__.py
│   ├── get_posts.py
│   │   ├── X                   ← username: @levelsio and @kepano
│   │   ├── Reddit              ← hot posts from r/AIUseCases, r/SideProject, r/Entrepreneur (AI business discussions), r/OpenAI, r/LocalLLaMA
│   │   ├── Discord
│   │   ├── HackerNews          ← "Show HN" posts
│
├── utils/                      ← Shared utilities
│   ├── __init__.py
│   ├── gsheet_writer.py        ← Functions to write data to Google Sheets
│   ├── openai_summariser.py    ← Function that sends content to OpenAI
```
