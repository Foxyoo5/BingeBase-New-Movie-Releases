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
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    # wait specifically for a poster image to show up in the grid
    try:
        page.wait_for_selector('img[alt*="poster"]', timeout=30000)
    except Exception as e:
        print(f"Warning: poster selector never appeared - {e}")
    # small extra buffer for any late-loading items
    page.wait_for_timeout(2000)
    html = page.content()
    # --- DEBUG: print diagnostic info to the Actions log ---
print(f"HTML length: {len(html)}")
print(f"Contains 'poster': {'poster' in html}")
print(f"Number of <img> tags: {html.count('<img')}")

# find the first image whose alt text mentions poster, and print raw context around it
idx = html.find('poster')
if idx != -1:
    print("--- Context around first 'poster' occurrence ---")
    print(html[max(0, idx-300):idx+300])
else:
    print("No 'poster' text found anywhere in the rendered HTML.")
# --- END DEBUG ---
    browser.close()

pattern = re.compile(
    r'data-media-card-target="posterLink"[^>]+href="(/movies/[^"]+)"[^>]*>\s*'
    r'<img[^>]+alt="([^"]+?) poster"[^>]+src="(https://cdn\.bingebase\.com/[^"]+)"'
)

matches = pattern.findall(html)[:20]

q = chr(34)
items_xml = ""

for href, title, poster in matches:
    title_clean = title.replace("&", "&amp;")
    link = f"https://bingebase.com{href}"
    items_xml += "<item>"
    items_xml += f"<title>{title_clean}</title>"
    items_xml += "<description>" + chr(60) + "![CDATA[" + \
        f'<img src=' + q + poster + q + '>' + \
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
