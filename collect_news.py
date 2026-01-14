import json
import feedparser
import time
from datetime import datetime
import urllib.parse
import ssl
import requests
import re
import concurrent.futures
import os

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
    { 'id': 'china', 'name': '知名町', 'keywords': ['知名町', '知名'] },
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
    { 'id': 'amami_oshima', 'name': '奄美大島', 'keywords': ['奄美大島', '奄美', '奄美群島'] }
]

ALLOWED_SOURCES = {
    'amamishimbun.co.jp': '奄美新聞',
    'nankainn.com': '南海日日新聞',
    'amami-minamisantou.keizai.biz': '奄美群島南三島経済新聞',
    'ryukyushimpo.jp': '琉球新報',
    '373news.com': '南日本新聞'
}

ALLOWED_SOURCE_NAMES = ['奄美新聞', '南海日日新聞', '奄美群島南三島経済新聞', '琉球新報', '琉球新報デジタル', '南日本新聞']
BLOCK_KEYWORDS = ['tag', 'list', 'category', 'archive', 'writer', 'photo', 'pr', 'ad', 'タグ', '一覧', 'まとめ', 'アーカイブ', '特集', '求人', '人事']

def parse_date(struct_time):
    if struct_time:
        return datetime.fromtimestamp(time.mktime(struct_time)).isoformat()
    return datetime.now().isoformat()

def get_google_news_rss(query):
    site_query = ' OR '.join([f'site:{domain}' for domain in ALLOWED_SOURCES.keys()])
    full_query = f'"{query}" AND ({site_query})'
    encoded_query = urllib.parse.quote(full_query)
    return f"https://news.google.com/rss/search?q={encoded_query}&hl=ja&gl=JP&ceid=JP:ja"

def fetch_feed(target_query):
    rss_url = get_google_news_rss(target_query)
    try:
        return feedparser.parse(rss_url)
    except Exception as e:
        print(f"Error fetching {target_query}: {e}")
        return None

def collect_news():
    all_articles = []
    seen_urls = set()
    
    print("Fetching news (Parallel Mode)...")
    
    search_targets = []
    for m in MUNICIPALITIES: search_targets.append(m['name'])
    for i in ISLANDS: search_targets.append(i['name'])
    search_targets = list(set(search_targets))
    
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
                    if any(k in title for k in BLOCK_KEYWORDS): continue
                    
                    source_name = "Google News"
                    if 'source' in entry and 'title' in entry.source:
                        source_name = entry.source.title
                    if source_name == '琉球新報デジタル': source_name = '琉球新報'
                    if source_name not in ALLOWED_SOURCE_NAMES: continue
                    
                    clean_title = title.replace('奄美群島南三島経済新聞', '')
                    
                    assigned_id = None
                    assigned_name = None
                    
                    for muni in MUNICIPALITIES:
                        if any(kw in clean_title for kw in muni['keywords']):
                            assigned_id = muni['id']
                            assigned_name = muni['name']
                            break 
                    
                    if not assigned_id:
                        for island in ISLANDS:
                            if any(kw in clean_title for kw in island['keywords']):
                                assigned_id = island['id']
                                assigned_name = island['name']
                                break
                    
                    if not assigned_id: continue
                    
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
                        'date': article_date,
                        'title': title,
                        'content': summary[:100] + '...',
                        'source': source_name,
                        'imageUrl': image_url,
                        'url': url
                    }
                    all_articles.append(article)
            except Exception as e:
                print(f"Error processing {query}: {e}")

    # Merge with existing data
    output_dir = 'news_data'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, 'news.json')
    existing_articles = []
    
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_articles = json.load(f)
                print(f"Loaded {len(existing_articles)} existing articles.")
        except json.JSONDecodeError:
            print("Existing news.json was corrupted, starting fresh.")

    # Deduplicate: Create a dict by URL to merge
    # New articles take precedence for content updates if we wanted, 
    # but technically old articles shouldn't change. 
    # We prioritize keeping OLD records (history) and adding NEW ones.
    
    article_map = {a['url']: a for a in existing_articles}
    new_count = 0
    
    for a in all_articles:
        if a['url'] not in article_map:
            article_map[a['url']] = a
            new_count += 1
    
    # Convert back to list
    final_list = list(article_map.values())
    
    # Sort by date (newest first)
    final_list.sort(key=lambda x: x['date'], reverse=True)
    
    print(f"Merged {new_count} new articles. Total: {len(final_list)}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)
    
    print(f"Saved to {output_path}")

if __name__ == '__main__':
    collect_news()

