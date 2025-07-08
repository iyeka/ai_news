import re
import utils
import config
import logging
from typing import Iterable
from playwright.async_api import async_playwright

config.setup_logger()

def extract_user_text(text:str) -> str:
    lines = text.split("\n")

    # Find the index of the date line (format: dd/dd/dd)
    date_index = None
    # e.g. 04/17/25, 3d, 12d, 3h, 10h, 5m, 30m
    date_pattern = re.compile(r"^(?:\d{2}/\d{2}/\d{2}|\d+d|\d+h|\d+m)$")

    for i, line in enumerate(lines):
        if date_pattern.match(line.strip()):
            date_index = i
            break

    if date_index is None:
        logging.warning(f"Date data is not found in the post. So the full inner_text '''{text}''' of the post will be return.")
        return text
    
    # Find the index of the "Translate" line
    translate_index = None
    for i, line in enumerate(lines):
        if line.strip() == "Translate":
            translate_index = i
            break

    if translate_index is None:
        logging.warning(f"User posting text is not found in the post. So the full inner_text '''{text}''' of the post will be return.")
        return text
    
    userlines = lines[date_index+1 : translate_index]
    return " ".join(userlines).strip()
    

async def get_posts(username):
    url = f"https://www.threads.net/@{username}"

    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0 Safari/537.36"
        ))
        page = await context.new_page()

        await page.goto(url)
        logging.debug("Get access to the {url}")
        await page.wait_for_selector('div[data-pressable-container="true"]')
        post_blocks = await page.query_selector_all('div[data-pressable-container="true"]')
        logging.info(f"🧵 {len(post_blocks)} posts found.")

        for post in post_blocks:
            text = await post.inner_text()
            user_text = extract_user_text(text)
            logging.info("Successfully extracted user posting text.")
            
            # starts with /@ and contains /post/
            link_line = await post.query_selector('a[href^="/@"][href*="/post/"]')
            href = await link_line.get_attribute("href")
            logging.debug(f"Successfully extracted href {href} from {link_line}.")
            full_link = f"https://www.threads.net{href}"

            date_line = await post_blocks[0].query_selector("time")
            date = await date_line.get_attribute("datetime")
            logging.debug(f"Successfully extracted {date} from {date_line}.")

            post = dict(
            date = date,
            author = f"@{username}",
            content = user_text,
            link = full_link,
            )
            logging.debug(f"This is the post. \n{post}")

            results.append(post)

        await browser.close()

    return results

async def get_multiple_users_posts(users: Iterable):
    results = []
    for user in users:
        logging.info(f"📥 Fetching posts from: {user}")
        posts = await get_posts(user)
        results.extend(posts)
    logging.info(f"{len(results)} posts are found.")
    return results

def get_base_url(url):
    match = re.search(r'/post/([a-zA-Z0-9_-]+)', url)
    logging.debug(f"matched post, {match} found.")
    return match.group(1)

async def main(users: Iterable):
    basesave = utils.BaseSave(sheet_name=config.THREADS_SHEET)
    await basesave.duplicated_or_save(users, get_multiple_users_posts, get_base_url)