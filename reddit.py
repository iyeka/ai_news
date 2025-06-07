import config
import utils
import re
from datetime import datetime

def get_base_url(url):
    match = re.search(r'/gallery/([a-z0-9]+)', url)
    return match.group(1)

def get_posts(community, limit=5):
    posts = []
    subreddit = config.reddit.subreddit(community)
    for submission in subreddit.hot(limit=limit):
        text_or_not = submission.is_self
        unix_timestamp = submission.created_utc
        dictionary = dict(
            date = datetime.fromtimestamp(unix_timestamp).isoformat(),
            community = f"r/{community}",
            title = submission.title,
            content = submission.selftext,
            link = f"https://www.reddit.com/gallery/{submission.id}",
        )
        posts.append(dictionary)

    return posts
    
def main(reddits):
    cl_basesave = utils.BaseSave(config.REDDIT_SHEET)
    cl_basesave.duplicated_or_save(keywords=reddits, fn_get_posts=get_posts, fn_get_base_url=get_base_url)
    
'''
def using_googletranslate(rows):
    # get rows
    headers = rows[0]
    data_rows = rows[1:]

    # get columns
    title_idx = headers.index("title")
    content_idx = headers.index("content")

    for row in data_rows:
        row[title_idx] = f'=GOOGLETRANSLATE("{row[title_idx]}", "en", "ko")'
        row[content_idx] = f'=GOOGLETRANSLATE("{row[content_idx]}", "en", "ko")'

    return data_rows
'''