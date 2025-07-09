#!/usr/bin/env python3
"""
geo_seo_blitz.py
24-hour SEO & LLM promotion blitz orchestrator.
"""

import os
import requests
from github import Github
import openai
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
import time

# Load environment variables
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
NETLIFY_BUILD_HOOK = os.getenv("NETLIFY_BUILD_HOOK")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BING_API_KEY = os.getenv("BING_API_KEY")
TARGET_DOMAIN = os.getenv("TARGET_DOMAIN")
TARGET_PATH = os.getenv("TARGET_PATH")
SITE_URL = f"https://{TARGET_DOMAIN}"
TARGET_URL = SITE_URL + TARGET_PATH

# Initialize GitHub & OpenAI clients
g = Github(GITHUB_TOKEN)
repo = g.get_repo(GITHUB_REPO)
openai.api_key = OPENAI_API_KEY

def trigger_netlify():
    if NETLIFY_BUILD_HOOK:
        requests.post(NETLIFY_BUILD_HOOK)
        print("🚀 Netlify deploy triggered")

def inject_jsonld():
    path = TARGET_PATH.lstrip('/')
    if not path:
        path = 'index.html'
    file = repo.get_contents(path, ref=GITHUB_BRANCH)
    html = file.decoded_content.decode()
    prompt = f"Inject full Hotel JSON-LD + meta tags into this HTML for {TARGET_URL}:\n{html}"
    resp = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":prompt}],
        temperature=0
    )
    updated = resp.choices[0].message.content
    repo.update_file(path, "chore: inject JSON-LD & meta", updated, file.sha, branch=GITHUB_BRANCH)
    print("✅ JSON-LD injected and committed")
    trigger_netlify()

def generate_blog_and_citations():
    prompt = f"Write a 300-word geo-targeted blog post about Fontainebleau in Miami Beach with links to {TARGET_URL}."
    resp = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":prompt}],
        temperature=0.7
    )
    content = resp.choices[0].message.content
    path = "blog/fontainebleau-miami-beach.md"
    try:
        file = repo.get_contents(path, ref=GITHUB_BRANCH)
        repo.update_file(path, "chore: update blog post", content, file.sha, branch=GITHUB_BRANCH)
    except:
        repo.create_file(path, "chore: add blog post", content, branch=GITHUB_BRANCH)
    print("✅ Blog post generated & committed")
    trigger_netlify()

def push_sitemap_and_recrawl():
    urls = [SITE_URL + "/", TARGET_URL, SITE_URL + "/blog/fontainebleau-miami-beach"]
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for u in urls:
        url = ET.SubElement(urlset, "url")
        ET.SubElement(url, "loc").text = u
        ET.SubElement(url, "lastmod").text = time.strftime("%Y-%m-%d")
    xml = ET.tostring(urlset, encoding="utf-8", method="xml").decode()
    path = "sitemap.xml"
    try:
        file = repo.get_contents(path, ref=GITHUB_BRANCH)
        repo.update_file(path, "chore: update sitemap", xml, file.sha, branch=GITHUB_BRANCH)
    except:
        repo.create_file(path, "chore: add sitemap", xml, branch=GITHUB_BRANCH)
    print("✅ sitemap.xml committed")
    trigger_netlify()
    endpoint = f"https://ssl.bing.com/webmaster/api.svc/json/SubmitUrlBatch?apikey={BING_API_KEY}"
    payload = {"siteUrl": SITE_URL, "urlList": urls}
    r = requests.post(endpoint, json=payload)
    if r.status_code == 200:
        print("✅ Submitted to Bing Webmaster for recrawl")
    else:
        print("❌ Bing recrawl failed", r.text)

def press_release_and_outreach():
    prompt = f"Write a press release for a major event at {TARGET_URL}. Include date, location, and link."
    resp = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":prompt}],
        temperature=0.7
    )
    with open("press_release.txt", "w") as f:
        f.write(resp.choices[0].message.content)
    print("✅ Press release drafted to press_release.txt")

def monitor_and_validate():
    r = requests.get(TARGET_URL).text
    if 'application/ld+json' in r:
        print("✅ JSON-LD detected on target page")
    else:
        print("❌ JSON-LD missing on target page")

if __name__ == '__main__':
    os.makedirs("blog", exist_ok=True)
    if not os.listdir("blog"):
        open("blog/.gitkeep", 'w').close()
    inject_jsonld()
    generate_blog_and_citations()
    push_sitemap_and_recrawl()
    press_release_and_outreach()
    monitor_and_validate()
    print("🎉 Geo SEO Blitz complete!")