from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import feedparser
import time
from datetime import datetime
import urllib.parse
import ssl
import requests
from bs4 import BeautifulSoup
import re
import concurrent.futures

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Basic Auth Configuration
import os
from functools import wraps
from flask import request, Response

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid."""
    env_user = os.environ.get('BASIC_AUTH_USER')
    env_pass = os.environ.get('BASIC_AUTH_PASSWORD')
    return username == env_user and password == env_pass

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Only require auth if env vars are set
        if not os.environ.get('BASIC_AUTH_USER'):
            return f(*args, **kwargs)
            
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# SSL fix
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

MUNICIPALITIES = [
    { 'id': 'amami', 'name': '奄美市', 'keywords': ['奄美市'] },
    { 'id': 'yamato', 'name': '大和村', 'keywords': ['大和村'] },
    { 'id': 'uken', 'name': '宇検村', 'keywords': ['宇検村'] },
    { 'id': 'setouchi', 'name': '瀬戸内町', 'keywords': ['瀬戸内町'] },
    { 'id': 'tatsugo', 'name': '龍郷町', 'keywords': ['龍郷町'] },
    { 'id': 'kikai', 'name': '喜界町', 'keywords': ['喜界町'] },
    { 'id': 'tokunoshima', 'name': '徳之島町', 'keywords': ['徳之島町'] },
    { 'id': 'amagi', 'name': '天城町', 'keywords': ['天城町'] },
    { 'id': 'isen', 'name': '伊仙町', 'keywords': ['伊仙町'] },
    { 'id': 'wadomari', 'name': '和泊町', 'keywords': ['和泊町'] },
    { 'id': 'china', 'name': '知名町', 'keywords': ['知名町', '知名'] }, # Allow "China" without "cho"
    { 'id': 'yoron', 'name': '与論町', 'keywords': ['与論町', '与論'] }
]

# Island Definitions (Fallback)
ISLANDS = [
    { 'id': 'kikai_jima', 'name': '喜界島', 'keywords': ['喜界島'] },
    { 'id': 'tokuno_shima', 'name': '徳之島', 'keywords': ['徳之島'] },
    { 'id': 'okino_erabu', 'name': '沖永良部島', 'keywords': ['沖永良部', '沖永良部島'] },
    { 'id': 'yoron_jima', 'name': '与論島', 'keywords': ['与論島'] },
    { 'id': 'kakeroma_jima', 'name': '加計呂麻島', 'keywords': ['加計呂麻島', '加計呂麻'] },
    { 'id': 'uke_jima', 'name': '請島', 'keywords': ['請島'] },
    { 'id': 'yoro_shima', 'name': '与路島', 'keywords': ['与路島'] },
    # Amami Oshima / Generic Amami (Fallback - Lowest Priority)
    { 'id': 'amami_oshima', 'name': '奄美大島', 'keywords': ['奄美大島', '奄美', '奄美群島'] }
]

# Strict Source List
ALLOWED_SOURCES = {
    'amamishimbun.co.jp': '奄美新聞',
    'nankainn.com': '南海日日新聞',
    'amami-minamisantou.keizai.biz': '奄美群島南三島経済新聞',
    'ryukyushimpo.jp': '琉球新報',
    '373news.com': '南日本新聞'
}

# Simplified Strict Source List names (must match RSS source.title approx)
ALLOWED_SOURCE_NAMES = ['奄美新聞', '南海日日新聞', '奄美群島南三島経済新聞', '琉球新報', '琉球新報デジタル', '南日本新聞']

# Keywords to exclude based on Title
BLOCK_KEYWORDS = ['tag', 'list', 'category', 'archive', 'writer', 'photo', 'pr', 'ad', 'タグ', '一覧', 'まとめ', 'アーカイブ', '特集', '求人', '人事']

def parse_date(struct_time):
    if struct_time:
        return datetime.fromtimestamp(time.mktime(struct_time)).isoformat()
    return datetime.now().isoformat()

def get_google_news_rss(query):
    # Construct a query targeting these specific sites
    site_query = ' OR '.join([f'site:{domain}' for domain in ALLOWED_SOURCES.keys()])
    full_query = f'"{query}" AND ({site_query})'
    encoded_query = urllib.parse.quote(full_query)
    return f"https://news.google.com/rss/search?q={encoded_query}&hl=ja&gl=JP&ceid=JP:ja"

def fetch_feed(target_query):
    rss_url = get_google_news_rss(target_query)
    try:
        # print(f"Fetching RSS for {target_query}")
        return feedparser.parse(rss_url)
    except Exception as e:
        print(f"Error fetching {target_query}: {e}")
        return None

@app.route('/api/news')
@requires_auth
def get_news():
    all_articles = []
    seen_urls = set()
    print("Fetching news (Parallel Mode with 8 Islands)...")
    
    search_targets = []
    for m in MUNICIPALITIES: search_targets.append(m['name'])
    for i in ISLANDS: search_targets.append(i['name'])
    search_targets = list(set(search_targets))
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_query = {executor.submit(fetch_feed, q): q for q in search_targets}
        
        for future in concurrent.futures.as_completed(future_to_query):
            query = future_to_query[future]
            try:
                feed = future.result()
                if not feed: continue
                
                for entry in feed.entries:
                    url = entry.link
                    if url in seen_urls: continue
                    article_date = parse_date(entry.published_parsed)
                    
                    article_dt = datetime.fromisoformat(article_date)
                    if (datetime.now() - article_dt).days > 365:
                        continue
                        
                    title = entry.title

                    # 1. Filter by Block Keywords

                    # 1. Filter by Block Keywords
                    if any(k in title for k in BLOCK_KEYWORDS):
                        continue

                    # 2. Strict Source Check
                    source_name = "Google News"
                    if 'source' in entry and 'title' in entry.source:
                        source_name = entry.source.title
                    
                    if source_name == '琉球新報デジタル': source_name = '琉球新報'

                    if source_name not in ALLOWED_SOURCE_NAMES:
                        continue
                    
                    # Clean title for keyword matching
                    # Remove the newspaper name if present to avoid false positives (e.g. "Amami...Keizai Shimbun" matching "Amami")
                    clean_title = title.replace('奄美群島南三島経済新聞', '')

                    # 3. Municipality/Island Assignment Logic
                    assigned_id = None
                    assigned_name = None
                    
                    # Priority 1: Specific Municipality Match
                    for muni in MUNICIPALITIES:
                        # Allow fuzzy "China" (without cho) but use clean_title
                        if any(kw in clean_title for kw in muni['keywords']):
                            assigned_id = muni['id']
                            assigned_name = muni['name']
                            break 
                    
                    # Priority 2: Island Match (Fallback)
                    if not assigned_id:
                        for island in ISLANDS:
                            if any(kw in clean_title for kw in island['keywords']):
                                assigned_id = island['id']
                                assigned_name = island['name']
                                break
                                
                    if not assigned_id:
                        continue
                    
                    seen_urls.add(url)

                    image_url = f"https://placehold.co/100x70/0099c6/FFF?text={assigned_name[:2]}"
                    summary = entry.summary if 'summary' in entry else ""
                    match = re.search(r'src="([^"]+)"', summary)
                    if match:
                        image_url = match.group(1)

                    article = {
                        'id': entry.guid if 'guid' in entry else entry.link,
                        'municipalityId': assigned_id,
                        'MunicipalityName': assigned_name,
                        'date': parse_date(entry.published_parsed),
                        'title': title, # Keep original title for display
                        'content': summary[:100] + '...',
                        'source': source_name,
                        'imageUrl': image_url,
                        'url': url
                    }
                    all_articles.append(article)
            except Exception as e:
                print(f"Error processing {query}: {e}")

    print(f"Entities fetched in {time.time() - start_time:.2f}s")
    all_articles.sort(key=lambda x: x['date'], reverse=True)
    return jsonify(all_articles)

@app.route('/news_data/<path:filename>')
@requires_auth
def serve_news_data(filename):
    return send_from_directory('news_data', filename)

@app.route('/favicon.png')
@requires_auth
def serve_favicon():
    return send_from_directory('.', 'favicon.png')

@app.route('/')
@requires_auth
def index():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    print("Server starting on http://localhost:5000")
    app.run(debug=True, port=5000, host='0.0.0.0')
