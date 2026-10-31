#!/usr/bin/env python3
"""Find and fetch freely licensed photos from Wikimedia Commons for stories.

    python3 tools/commons.py cat "Abbeville, Louisiana"     # files + subcategories
    python3 tools/commons.py search "Vermilion River"       # full-text file search
    python3 tools/commons.py get "File:Some photo.jpg" slug  # download + print front matter

Only public domain, CC0, CC BY and CC BY-SA files are accepted; anything else
(NC, ND, fair use, unknown) is refused. `get` saves a 1400px-wide copy to
img/photos/<slug>.<ext> and prints the image/image_credit lines to paste into
the story, with the author and license exactly as Commons records them.
"""
import json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

API = 'https://commons.wikimedia.org/w/api.php'
UA = 'VermilionTimes/1.0 (https://thevermiliontimes.com; news@thevermiliontimes.com)'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OK = re.compile(r'^(public domain|pd\b|cc0|cc by(-sa)? [\d.]+|cc by(-sa)?$|cc-by(-sa)?-[\d.]+)', re.I)

def fetch(url, timeout=30):
    # Commons rate-limits bursts (HTTP 429); wait and retry politely.
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 5: raise
            wait = int(e.headers.get('Retry-After') or 0) or 5 * 2 ** attempt
            print(f'(Commons asked us to slow down; waiting {wait}s)', file=sys.stderr); time.sleep(min(wait, 90))

def api(**params):
    params.update(format='json', formatversion='2', maxlag='5')
    return json.loads(fetch(API + '?' + urllib.parse.urlencode(params)))

def strip(html):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', html or '')).strip()

def info(pages):
    for p in pages:
        if p.get('ns') == 14:
            print(f'  [category] {p["title"]}'); continue
        ii = (p.get('imageinfo') or [{}])[0]; m = ii.get('extmetadata', {})
        lic = strip(m.get('LicenseShortName', {}).get('value'))
        mark = 'OK ' if OK.match(lic) and not re.search(r'\b(nc|nd)\b', lic, re.I) else 'NO '
        print(f'  {mark}{p["title"]} | {ii.get("width")}x{ii.get("height")} | {lic} | {strip(m.get("Artist", {}).get("value"))[:50]}')

def props():
    return dict(prop='imageinfo', iiprop='size|extmetadata|url|mime')

def main():
    if len(sys.argv) < 3: sys.exit(__doc__)
    cmd, arg = sys.argv[1], sys.argv[2]
    if cmd == 'cat':
        title = arg if arg.startswith('Category:') else 'Category:' + arg
        d = api(action='query', generator='categorymembers', gcmtitle=title, gcmtype='file|subcat', gcmlimit='60', **props())
        info(d.get('query', {}).get('pages', []))
    elif cmd == 'search':
        d = api(action='query', generator='search', gsrnamespace='6', gsrlimit='30', gsrsearch=arg + ' filetype:bitmap', **props())
        info(d.get('query', {}).get('pages', []))
    elif cmd == 'get':
        slug = sys.argv[3] if len(sys.argv) > 3 else sys.exit('get needs a slug')
        title = arg if arg.startswith('File:') else 'File:' + arg
        d = api(action='query', titles=title, iiurlwidth='1400', **props())
        p = d['query']['pages'][0]; ii = p['imageinfo'][0]; m = ii['extmetadata']
        lic = strip(m.get('LicenseShortName', {}).get('value'))
        if not OK.match(lic) or re.search(r'\b(nc|nd)\b', lic, re.I):
            sys.exit(f'REFUSED: license is "{lic}". Use public domain, CC0, CC BY or CC BY-SA only.')
        artist = strip(m.get('Artist', {}).get('value')) or 'Unknown author'
        url = ii.get('thumburl') or ii['url']
        ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower() or '.jpg'
        if ext not in ('.jpg', '.jpeg', '.png', '.webp'): ext = '.jpg'
        out = os.path.join(ROOT, 'img', 'photos', slug + ext)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        data = fetch(url, timeout=60)
        with open(out, 'wb') as f: f.write(data)
        page = 'https://commons.wikimedia.org/wiki/' + urllib.parse.quote(p['title'].replace(' ', '_'))
        credit = f'{artist} / Wikimedia Commons, {lic}' if not lic.lower().startswith(('public domain', 'pd')) else f'{artist} / Wikimedia Commons (public domain)'
        print(f'saved {os.path.relpath(out, ROOT)} ({os.path.getsize(out)//1024} KB)\n')
        print('Paste into the story front matter (write image_alt and caption yourself, describing only what the photo shows):')
        print(f'image: /img/photos/{slug}{ext}')
        print('image_alt: ')
        print('image_caption: ')
        print(f'image_credit: {credit}')
        print(f'image_source: {page}')
        print(f'\nDescription on Commons: {strip(m.get("ImageDescription", {}).get("value"))[:300]}')
        print(f'Date: {strip(m.get("DateTimeOriginal", {}).get("value"))}')
    else:
        sys.exit(__doc__)

if __name__ == '__main__':
    main()
