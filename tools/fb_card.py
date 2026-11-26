#!/usr/bin/env python3
"""Make a Facebook card (1080x1350 PNG) for a story: photo on top, headline under it
(Brison, Nov. 21, 2026), nameplate in the bottom bar.

    python3 tools/fb_card.py --slug <story-slug> --kicker "Starbase Louisiana" \
        --headline "..." --deck "..." --photo img/photos/x.jpg --credit "Photo: ..." 

Writes img/social/<slug>.png (served at https://thevermiliontimes.com/img/social/<slug>.png).
--photo must be a real licensed photo; engravings are refused. Uses Playwright's Chromium via node.
"""
import argparse, datetime, html, os, subprocess, tempfile, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = '/opt/pw-browsers/chromium-1243/chrome-linux64/chrome'
ap = argparse.ArgumentParser()
for a in ('slug', 'kicker', 'headline', 'deck', 'photo'): ap.add_argument('--' + a, required=True)
ap.add_argument('--credit', default='')
ap.add_argument('--date', default='')
ap.add_argument('--pos', default='center 40%', help='CSS background-position for the photo crop, e.g. "center 20%"')
ap.add_argument('--fit', default='cover', choices=['cover', 'whole'], help="'whole' shows the entire image uncropped across the top (for title graphics); 'cover' crops to fill")
a = ap.parse_args()
if '/img/cuts/' in a.photo or a.photo.startswith('img/cuts'):
    raise SystemExit('No engravings on Facebook cards (Brison, Nov. 14). Find a real licensed photo first.')
if 'aerial' in a.photo.lower():
    raise SystemExit('No aerial photos on cards (Brison, Nov. 21). Use a strong ground-level photo of the subject.')
e = lambda s: html.escape(s, quote=True)
date = a.date or datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-6))).strftime('%A, %B %-d, %Y')
photo = 'file://' + os.path.abspath(os.path.join(ROOT, a.photo.lstrip('/')))
photo_html = f'<img class="whole" src="{photo}">' if a.fit == 'whole' else '<div class="photo"></div>'
hlen = len(a.headline)
hsize = 78 if hlen < 45 else 68 if hlen < 70 else 60 if hlen < 95 else 52 if hlen < 125 else 46
if a.fit == 'whole': hsize = int(hsize * 1.2)
extra_css = '.text{flex:1;display:flex;flex-direction:column;justify-content:center;padding-top:0}.deck{font-size:34px}' if a.fit == 'whole' else ''
page = f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1350px;background:#fff;font-family:Georgia,'Times New Roman',serif;color:#111;position:relative;overflow:hidden}}
.wrap{{position:absolute;inset:0 0 96px;display:flex;flex-direction:column}}
.photo{{flex:1;min-height:560px;background:#ddd url('{photo}') {e(a.pos)}/cover no-repeat}}
.whole{{display:block;width:100%;height:auto}}
{extra_css}
.cred{{font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;font-size:16px;color:#666;padding:8px 56px 0;text-align:right;min-height:26px}}
.text{{padding:14px 56px 34px}}
.kick{{font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;font-size:24px;font-weight:bold;letter-spacing:5px;text-transform:uppercase;color:#b5121b;margin:0 0 14px}}
.hed{{font-size:{hsize}px;line-height:1.05;font-weight:bold;letter-spacing:-1px}}
.deck{{font-size:30px;line-height:1.35;color:#333;margin-top:18px;font-style:italic}}
.foot{{position:absolute;left:0;right:0;bottom:0;height:96px;background:#111;color:#fff;display:flex;align-items:center;justify-content:space-between;padding:0 56px}}
.foot b{{font-family:Georgia,'Times New Roman',serif;font-size:44px;letter-spacing:-0.5px}}.foot b span{{color:#ff5b62}}
.foot i{{font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;font-style:normal;font-size:22px;color:#ddd;letter-spacing:1px}}
</style></head><body><div class="wrap">
{photo_html}
<div class="cred">{e(a.credit)}</div>
<div class="text">
<div class="kick">&#9679; {e(a.kicker)}</div>
<div class="hed">{e(a.headline)}</div>
<div class="deck">{e(a.deck)}</div>
</div>
</div><div class="foot"><b>The <span>Vermilion</span> Times</b><i>thevermiliontimes.com</i></div></body></html>"""
os.makedirs(os.path.join(ROOT, 'img', 'social'), exist_ok=True)
out = os.path.join(ROOT, 'img', 'social', a.slug + '.png')
with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False) as f:
    f.write(page); src = f.name
js = f"""const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch({{executablePath:{json.dumps(CHROME)}}});
const p=await b.newPage({{viewport:{{width:1080,height:1350}}}});await p.goto('file://{src}');await p.waitForTimeout(400);
await p.screenshot({{path:{json.dumps(out)}}});await b.close()}})()"""
subprocess.run(['node', '-e', js], check=True, cwd='/tmp')
print(os.path.relpath(out, ROOT))
