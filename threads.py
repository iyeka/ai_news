import config
from typing import Iterable
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
import feedparser

class rss_generator():
    def __init__(self):
        self.cookie_file = "rss_app_cookies.json"

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
                await page.goto(config.rss_login_url)
                input("log in manually, then press Enter here.")
                await self.save_cookies(context)

            for username in usernames:
                profile_url = f"https://www.threads.net/@{username}"
                await page.goto(config.rss_generator_url)

                await page.locator("input.MuiAutocomplete-input").fill(profile_url)
                await page.click("button[type='submit']")
                print(f"making url for {username}... please wait.")

                await page.get_by_role("button", name="Save Feed").click()
                
                rss_url = await page.locator("input.Mui-readOnly").get_attribute("value")
                rss_urls.append(rss_url)
            
            await browser.close()
        
        return rss_urls

def get_posts(urls:list) -> list[dict]:
    posts=[]

    for url in urls:
        print(f"parsing {url}...")
        feed = feedparser.parse(url)
        for entry in feed.entries:
            post = dict(
            date = entry.get("published"),
            author = entry.get("author"),
            content = entry.get("summary"),
            link = entry.get("link"),
            )
            posts.append(post)

    return posts

usernames = ["choi.openai", "obj.moss"]
def main(usernames):
    urls = asyncio.run(rss_generator().get_rss_urls(usernames))
    posts = get_posts(urls)