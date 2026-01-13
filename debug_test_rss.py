import feedparser
import urllib.parse
import ssl

# Fix SSL context for some windows envs
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

def test_rss(query_str):
    print(f"\nTesting Query: {query_str}")
    encoded = urllib.parse.quote(query_str)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=ja&gl=JP&ceid=JP:ja"
    print(f"URL: {url}")
    
    try:
        feed = feedparser.parse(url)
        print(f"Status: {feed.status if 'status' in feed else 'Unknown'}")
        print(f"Entries found: {len(feed.entries)}")
        
        if len(feed.entries) > 0:
            print("Top article:", feed.entries[0].title)
            print("Source:", feed.entries[0].source.title if 'source' in feed.entries[0] else 'Unknown')
        else:
            print("No entries.")
            
    except Exception as e:
        print(f"Error: {e}")

# The query currently causing issues (simplified version from step 128)
q_complex = '奄美市 AND ("奄美新聞" OR "南海日日新聞" OR "南日本新聞" OR "奄美群島南三島経済新聞" OR "MBC" OR "KTS") -タグ -一覧 -まとめ -アーカイブ -PR'

# A simpler one
q_simple = '奄美市 AND ("奄美新聞" OR "南海日日新聞")'

test_rss(q_complex)
test_rss(q_simple)
