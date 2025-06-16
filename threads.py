import re
import utils
import config
import json
import feedparser
from typing import Iterable
from pathlib import Path
from playwright.async_api import async_playwright, expect, TimeoutError
from bs4 import BeautifulSoup

class rss_generator():
    def __init__(self):
        self.cookie_file = "rss_app_cookies.json"
        self.rss_login_url = "https://rss.app/signin"
        self.rss_generator_url = "https://rss.app/new-rss-feed"
        self.myfeeds = "https://rss.app/myfeeds"

    async def save_cookies(self, context):
        cookies = await context.storage_state()
        with open(self.cookie_file, "w") as file:
            json.dump(cookies, file)

    async def load_cookies(self):
        if Path(self.cookie_file).exists():
            with open(self.cookie_file) as file:
                return json.load(file)
        return None

    async def get_rss_urls(self, usernames:Iterable) -> list:
        rss_urls = []

        async with async_playwright() as p:
            if Path(self.cookie_file).exists():
                print("Login info found!")
                browser = await p.chromium.launch()
                context = await browser.new_context(storage_state=await self.load_cookies())
                page = await context.new_page()
            else:
                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context()
                page = await context.new_page()

                # If cookies don't exist, login manually once
                await page.goto(self.rss_login_url)
                input("log in manually, then press Enter here.")
                await self.save_cookies(context)

            for username in usernames:
                profile_url = f"https://www.threads.net/@{username}"
                await page.goto(self.rss_generator_url)

                search_input = page.locator("input.MuiAutocomplete-input")
                await search_input.fill(profile_url)
                await expect(search_input).to_have_value(profile_url)

                await page.click("button[type='submit']")
                print(f"making url for {username}... please wait.")

                try:
                    await page.get_by_role("button", name="Save Feed").click()
                except TimeoutError:
                    alert = page.locator("div.MuiAlert-message")
                    if await alert.is_visible():
                        print(alert.text_content())
                        break

                rss_url = await page.locator("input.Mui-readOnly").get_attribute("value")
                rss_urls.append(rss_url)
                
            await browser.close()
        
        return rss_urls
    
    async def delete_feed(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(storage_state=await self.load_cookies())
            page = await context.new_page()

            await page.goto(self.myfeeds)
            await page.click("button[ga='feed-menu]")
            await page.click("li[ga='menu-delete-feed']")

            await browser.close()

def get_posts(urls:list) -> list[dict]:
    def extract_text(html):
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            return text.replace("\n", " ")

    posts=[]
    for url in urls:
        print(f"parsing {url}...")
        feed = feedparser.parse(url)
        for entry in feed.entries:
            post = dict(
            date = entry.get("published"),
            author = entry.get("author"),
            content = extract_text(entry.get("summary")),
            link = entry.get("link"),
            )
            posts.append(post)

    return posts

def get_base_url(url):
    match = re.search(r'/post/([a-zA-Z0-9_-]+)', url)
    return match.group(1)

async def main(users):
    urls = await rss_generator().get_rss_urls(users)
    utils.BaseSave(sheet_name=config.THREADS_SHEET).duplicated_or_save(urls, get_posts, get_base_url)
    await rss_generator().delete_feed()