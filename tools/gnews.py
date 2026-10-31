#!/usr/bin/env python3
"""Sweep Google News for parish news and print each item's real article URL.

    python3 tools/gnews.py                    # the standard feeler queries, last 2 days
    python3 tools/gnews.py "Pecan Island" 5   # one query, last 5 days

Google News RSS links are redirects; this resolves them to the publisher's
URL so the story can be opened and read before anything is written.
"""
import html, json, re, sys, urllib.parse, urllib.request

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'}
QUERIES = ['Vermilion Parish', 'Starbase Louisiana', 'SpaceX Pecan Island', 'Vermilion Parish Sheriff', 'Abbeville Louisiana',
           'Kaplan Louisiana', 'Erath Louisiana', 'Gueydan', 'Delcambre', 'Maurice Louisiana', 'Intracoastal City']

def get(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    return urllib.request.urlopen(req, timeout=25).read().decode('utf-8', 'replace')

def resolve(link):
    aid = link.split('/articles/')[1].split('?')[0]
    try:
        page = get(f'https://news.google.com/rss/articles/{aid}')
        sig = re.search(r'data-n-a-sg="([^"]+)"', page).group(1)
        ts = re.search(r'data-n-a-ts="([^"]+)"', page).group(1)
        inner = f'["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],"X","X",1,[1,1,1],1,1,null,0,0,null,0],"{aid}",{ts},"{sig}"]'
        body = 'f.req=' + urllib.parse.quote(json.dumps([[['Fbv4je', inner]]]))
        out = get('https://news.google.com/_/DotsSplashUi/data/batchexecute', body.encode(),
                  {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'})
        return json.loads(json.loads(out.split('\n\n')[1])[0][2])[1]
    except Exception:
        return link

def main():
    queries = [sys.argv[1]] if len(sys.argv) > 1 else QUERIES
    days = sys.argv[2] if len(sys.argv) > 2 else '2'
    seen = set()
    for q in queries:
        feed = get('https://news.google.com/rss/search?' + urllib.parse.urlencode({'q': f'{q} when:{days}d', 'hl': 'en-US', 'gl': 'US', 'ceid': 'US:en'}))
        for it in re.findall(r'<item>(.*?)</item>', feed, re.S):
            title = html.unescape(re.search(r'<title>(.*?)</title>', it).group(1))
            if title in seen: continue
            seen.add(title)
            date = re.search(r'<pubDate>(.*?)</pubDate>', it).group(1)[:16]
            print(f'{date} | {title}\n    {resolve(re.search(r"<link>(.*?)</link>", it).group(1))}')

if __name__ == '__main__':
    main()
