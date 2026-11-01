#!/usr/bin/env python3
"""Post newly published stories to The Vermilion Times Facebook Page.

Run by .github/workflows/facebook.yml on every push to main. It finds article
files added in the push, waits for each page to go live on the site, then posts
the headline, deck and link to the Page through Facebook's Graph API.

Needs two GitHub repository secrets (Settings > Secrets and variables > Actions):
  FB_PAGE_ID     the Page's numeric ID
  FB_PAGE_TOKEN  a long-lived Page access token with pages_manage_posts
Without them it does nothing. Never put the token in this repository.
"""
import json, os, re, subprocess, sys, time, urllib.error, urllib.parse, urllib.request

SITE = 'https://thevermiliontimes.com'

def added_articles(before, after):
    if not before or set(before) == {'0'}:
        return []
    out = subprocess.run(['git', 'diff', '--name-only', '--diff-filter=A', before, after, '--', 'articles/'],
                         capture_output=True, text=True, check=True).stdout.split()
    return [f for f in out if re.match(r'articles/\d{4}-\d\d-\d\d-.+\.md$', f)]

def front(path):
    text = open(path, encoding='utf-8').read()
    m = re.match(r'---\n(.*?)\n---', text, re.S)
    meta = {}
    for line in (m.group(1) if m else '').splitlines():
        k, sep, v = line.partition(':')
        if sep and not line.startswith((' ', '-')):
            meta[k.strip()] = v.strip().strip('"')
    return meta

def live(url, title, wait=900):
    end = time.time() + wait
    while time.time() < end:
        try:
            page = urllib.request.urlopen(url, timeout=20).read().decode('utf-8', 'replace')
            if title.split()[0] in page:
                return True
        except Exception:
            pass
        time.sleep(30)
    return False

def main():
    page, token = os.environ.get('FB_PAGE_ID'), os.environ.get('FB_PAGE_TOKEN')
    if not page or not token:
        print('Facebook secrets not set; skipping. See tools/fb_post.py.')
        return
    failed = False
    for f in added_articles(os.environ.get('BEFORE', ''), os.environ.get('AFTER', 'HEAD')):
        meta = front(f)
        if meta.get('draft', '').lower() in ('yes', 'true'):
            continue
        url = f"{SITE}/news/{os.path.basename(f)[11:-3]}/"
        title = meta.get('title', '')
        if not live(url, title):
            print(f'not live yet, skipped: {url}'); continue
        body = urllib.parse.urlencode({'message': f"{title}\n\n{meta.get('deck', '')}", 'link': url,
                                       'access_token': token}).encode()
        try:
            r = json.load(urllib.request.urlopen(f'https://graph.facebook.com/{page}/feed', body, timeout=30))
            print('posted', url, r.get('id'))
        except urllib.error.HTTPError as e:
            print('Facebook refused', url, e.read().decode()[:300]); failed = True
    if failed:
        sys.exit(1)

if __name__ == '__main__':
    main()
