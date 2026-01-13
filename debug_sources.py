import feedparser
import urllib.parse
import ssl

if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

def check_sources(query):
    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=ja&gl=JP&ceid=JP:ja"
    print(f"Fetching: {url}")
    feed = feedparser.parse(url)
    
    sources = set()
    print(f"Found {len(feed.entries)} articles.")
    for entry in feed.entries:
        if 'source' in entry:
            sources.add(entry.source.title)
        else:
            # Try to parse from title if source field is missing
            title = entry.title
            last_dash = title.lastIndexOf(' - ') if 'lastIndexOf' in title else title.rfind(' - ')
            if last_dash > 0:
                sources.add(title[last_dash+3:])
    
    return sources

queries = [
    "奄美群島", 
    "奄美群島南三島経済新聞",
    "site:amami-minamisantou.keizai.biz",
    "徳之島"
]

for q in queries:
    print(f"\n--- Checking Query: {q} ---")
    found = check_sources(q)
    print("Sources found:", found)
