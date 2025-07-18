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

    # Save and load login information of RSS.app.
    async def save_cookies(self, context):
        cookies = await context.storage_state()
        with open(self.cookie_file, "w") as file:
            json.dump(cookies, file)

    async def load_cookies(self):
        if Path(self.cookie_file).exists():
            with open(self.cookie_file) as file:
                return json.load(file)
        return None

    async def get_rss_url(self, username:str) -> str:
        async with async_playwright() as p:
            if Path(self.cookie_file).exists():
                print("Login info found🫡")
                browser = await p.chromium.launch()
                context = await browser.new_context(storage_state=await self.load_cookies())
                page = await context.new_page()
            else:
                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context()
                page = await context.new_page()

                # If cookies don't exist, login manually once
                await page.goto(self.rss_login_url)
                input("Log in manually, then press Enter here.")
                try:
                    await page.wait_for_url("https://rss.app/myfeeds")
                    await self.save_cookies(context)
                except:
                    print(f"❌ Login failed. Current URL: {page.url}")

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
                    alert_message = await alert.text_content()
                    raise SystemExit(alert_message)

            rss_url = await page.locator("input.Mui-readOnly").get_attribute("value")
                
            await browser.close()
        
        return rss_url
    
    async def delete_feed(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(storage_state=await self.load_cookies())
            page = await context.new_page()

            await page.goto(self.myfeeds)
            await page.click('button[ga="feed-menu"]')
            await page.click('li[ga="menu-delete-feed"]')

            heading = page.locator("h2", has_text="delete")
            await heading.wait_for()
            await page.click('button[ga="feed-delete-submit"]')
            await page.wait_for_timeout(2000)
            print("feed deleting succeed.")

            await browser.close()

def get_posts(url:str) -> list[dict]:
    def extract_text(html):
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        return text.replace("\n", " ")

    posts=[]
    print(f"parsing {url}...")
    feed = feedparser.parse(url)
    for entry in feed.entries:
        summary = entry.get("summary")
        if not summary:
            continue
        post = dict(
            date = entry.get("published"),
            author = entry.get("author"),
            content = extract_text(summary),
            link = entry.get("link"),
        )
        posts.append(post)

    return posts

def get_base_url(url):
    match = re.search(r'/post/([a-zA-Z0-9_-]+)', url)
    return match.group(1)

async def main(users):
    for user in users:
        url = await rss_generator().get_rss_url(user)
        utils.BaseSave(sheet_name=config.THREADS_SHEET).duplicated_or_save(url, get_posts, get_base_url)
        await rss_generator().delete_feed()