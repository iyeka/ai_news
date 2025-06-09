import feedparser
import asyncio
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

rss_login_url = "https://rss.app/signin"
rss_generator_url = "https://rss.app/new-rss-feed"

cookie_file = "rss_app_cookies.json"
usernames = ["choi.openai", "bocchi.ai", "mock_jokerbug", "ymzinvest", "obj.moss", "smilegoodthings", "quady.openai", "cuticogent", "anelo_96", "heo_intern", "aiowner_"]

def save_cookies(context):
    cookies = context.storage_state()
    with open(cookie_file, "w") as file:
        json.dump(cookies, file)

def load_cookies():
    if Path(cookie_file).exists():
        with open(cookie_file) as file:
            return json.load(file)
    return None

def get_rss_urls(username):
    rss_urls = []

    with sync_playwright() as p:
        if Path(cookie_file).exists():
            print("Login info found!")
            browser = p.chromium.launch()
            context = browser.new_context(storage_state=load_cookies())
            page = context.new_page()
        else:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            # If cookies don't exist, login manually once
            page.goto(rss_login_url)
            input("log in manually, then press Enter here.")
            save_cookies(context)

        profile_url = f"https://www.threads.net/@{username}"
        page.goto(rss_generator_url)
        print("fetching urls... please wait.")

        page.locator("input.MuiAutocomplete-input").wait_for()
        page.fill("input.MuiAutocomplete-input", profile_url)
        page.click("button[type='submit']")

        generate_rss_url = page.get_by_role("button", name="Save Feed")
        generate_rss_url.wait_for()
        generate_rss_url.click()
        
        rss_url_input = page.locator("input.Mui-readOnly")
        rss_url_input.wait_for()
        rss_url = rss_url_input.get_attribute("value")

        rss_urls.append(rss_url)
        
        browser.close()
    
    return rss_urls

print(get_rss_urls("choi.openai"))