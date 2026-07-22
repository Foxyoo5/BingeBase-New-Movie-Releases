import re
import os
import datetime
from playwright.sync_api import sync_playwright

current_year = datetime.datetime.utcnow().year

url = (
    f"https://bingebase.com/movies/new-releases"
    f"?sort=recent&year_from={current_year}&year_to="
    f"&country%5B%5D=US&country%5B%5D=GB&language%5B%5D=en"
)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(user_agent="Mozilla/5.0 (compatible; RSSFeedBot/1.0)")
    page.goto(url, wait_until="networkidle", timeout=60000)
    # give the JS-rendered grid a moment to fully populate
    page.wait_for_timeout(3000)
    html = page.content()
    browser.close()

pattern = re.compile(
    r'<img[^>]+alt="([^"]+?) poster"[^>]+src="(https://cdn\.bingebase\.com/[^"]+)"[^>]*>'
    r'.*?href="(https://bingebase\.com/movies/[^"]+)"'
    r'.*?<h3[^>]*>\s*([\d.]+)\s+.*?\((\d{4})\)',
    re.DOTALL
)

matches = pattern.findall(html)[:20]

q = chr(34)
items_xml = ""

for title, poster, link, rating, year in matches:
    title_clean = title.replace("&", "&amp;")
    items_xml += "<item>"
    items_xml += f"<title>{title_clean}</title>"
    items_xml += "<description>" + chr(60) + "![CDATA[" + \
        f'<img src=' + q + poster + q + f'><br>Rating: {rating}' + \
        "]]" + chr(62) + "</description>"
    items_xml += f"<link>{link}</link>"
    items_xml += "</item>"

rss = '<?xml version=' + q + '1.0' + q + ' encoding=' + q + 'UTF-8' + q + '?>'
rss += "<rss version=" + q + "2.0" + q + ">"
rss += "<channel>"
rss += "<title>New Movie Releases</title>"
rss += "<link>https://foxyoo5.github.io/New-Movie-Releases/new-movie-releases.xml</link>"
rss += "<description>Latest movie releases from BingeBase</description>"
rss += items_xml
rss += "</channel></rss>"

os.makedirs("docs", exist_ok=True)
with open("docs/new-movie-releases.xml", "w", encoding="utf-8") as f:
    f.write(rss)

print(f"Found {len(matches)} movies")
