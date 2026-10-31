#!/usr/bin/env python3
"""Check that a story is written in our own words, not copied from its sources.

    python3 tools/originality.py articles/2026-10-31-some-story.md

Fetches every URL in the story's `sources:`, strips quoted material (short,
attributed quotes are allowed), and reports any run of 7 or more words the
story shares with a source. Official names (agencies, bills) can trip it;
everything else must be rewritten until the check passes (exit code 0).
"""
import html, re, sys, urllib.request
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'}
N, LIMIT = 7, 3

def words(t): return re.findall(r"[a-z0-9$']+", t.lower())
def strip_quotes(t): return re.sub(r'["“][^"”]{0,160}["”]', ' ', t)

def fetch(url):
    for u in (url, url.rstrip('/') + '/amp/'):
        try:
            raw = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25).read().decode('utf-8', 'replace')
            paras = re.findall(r'<p[^>]*>(.*?)</p>', raw, re.S)
            text = ' '.join(html.unescape(re.sub('<[^>]+>', ' ', p)) for p in paras)
            if len(text) > 400: return text
        except Exception:
            continue
    return ''

def main():
    if len(sys.argv) < 2: sys.exit(__doc__)
    raw = open(sys.argv[1], encoding='utf-8').read()
    fm, body = raw.split('---', 2)[1], raw.split('---', 2)[2]
    urls = [l.split('|', 1)[1].strip() for l in fm.splitlines() if l.startswith('- ') and '|' in l]
    mine = words(strip_quotes(body))
    worst = 0
    for url in urls:
        src = fetch(url)
        if not src:
            print(f'?  could not read {url} (check it by eye)'); continue
        grams = {tuple(s) for s in (words(strip_quotes(src))[i:i + N] for i in range(len(words(strip_quotes(src))) - N + 1))}
        hits = sorted({' '.join(mine[i:i + N]) for i in range(len(mine) - N + 1) if tuple(mine[i:i + N]) in grams})
        worst = max(worst, len(hits))
        print(f'{"OK " if len(hits) <= LIMIT else "COPY"} {len(hits):3d} shared {N}-word runs with {url}')
        for h in hits[:12]: print('      ', h)
    if worst > LIMIT:
        sys.exit('Rewrite the flagged passages in your own words, then run this again.')

if __name__ == '__main__':
    main()
