import os
import praw
from dotenv import load_dotenv
from openai import OpenAI
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Load variables from .env into environment
load_dotenv()

# OpenAI settings
OPENAI_MODEL_NAME="gpt-4o-mini"
api_key = os.getenv("OPENAI_API_KEY")

def get_client():
    return OpenAI(api_key=api_key)

# Google Sheets API settings
CREDENTIALS_FILE = 'credentials.json'

SPREADSHEET_ID = '1qr_CluX6H4sUEfHwbntpRhj4kj2ldTaCENN00IT-8rg'
YOUTUBE_SHEET = 'youtube'
X_SHEET = 'x'
REDDIT_SHEET = 'reddit'

def setup_google_sheets_api():

    creds = service_account.Credentials.from_service_account_file(
    CREDENTIALS_FILE,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
    )

    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    return sheet

# X settings
nitter_servers = ["xcancel.com", "nitter.poast.org", "nitter.privacydev.net"]

# Reddit settings
client_id=os.getenv("CLIENT_ID")
client_secret=os.getenv("CLIENT_SECRET")
user_agent=os.getenv("USER_AGENT")

reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    user_agent=user_agent,
)

# Threads settings
rss_login_url = "https://rss.app/signin"
rss_generator_url = "https://rss.app/new-rss-feed"