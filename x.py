import re
import feedparser
import utils
import config

def get_base_url(url):
    match = re.search(r'/status/(\d+)', url)
    return match.group(1)

def get_posts(username):
    url = f"https://xcancel.com/{username}/rss"
    feed = feedparser.parse(url)

    posts = []
    for entry in feed.entries:
        link = entry.link
        base_link = get_base_url(link)
        dictionary = dict(
            date = entry.published,
            author = entry.author,
            title = entry.title,
            content = entry.summary,
            link = f"https://x.com/{username}/status/{base_link}" if base_link else link
        )
        posts.append(dictionary)
    return posts
    
def main(users):
    cl_basesave = utils.BaseSave(sheet_name=config.X_SHEET)
    cl_basesave.duplicated_or_save(keywords=users, fn_get_posts=get_posts, fn_get_base_url=get_base_url)