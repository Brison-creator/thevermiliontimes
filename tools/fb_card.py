#!/usr/bin/env python3
"""Make a newspaper-style Facebook card (1080x1350 PNG) for a story.

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
a = ap.parse_args()
if '/img/cuts/' in a.photo or a.photo.startswith('img/cuts'):
    raise SystemExit('No engravings on Facebook cards (Brison, Nov. 14). Find a real licensed photo first.')
e = lambda s: html.escape(s, quote=True)
date = a.date or datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-6))).strftime('%A, %B %-d, %Y')
photo = 'file://' + os.path.abspath(os.path.join(ROOT, a.photo.lstrip('/')))
cut = '/img/cuts/' in a.photo
hlen = len(a.headline)
hsize = 76 if hlen < 60 else 66 if hlen < 90 else 58 if hlen < 120 else 50
page = f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1350px;background:#fff;font-family:Georgia,'Times New Roman',serif;color:#111;position:relative;overflow:hidden}}
.wrap{{position:absolute;inset:0 0 78px;padding:44px 56px 0;display:flex;flex-direction:column}}
.mast{{text-align:center;border-top:6px double #111;border-bottom:2px solid #111;padding:22px 0 18px}}
.mast h1{{font-size:84px;font-weight:bold;letter-spacing:-1.5px;line-height:1}}
.mast h1 span{{color:#b5121b}}
.tag{{font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;font-size:20px;letter-spacing:6px;text-transform:uppercase;color:#b5121b;font-weight:bold;margin-top:14px}}
.date{{display:flex;justify-content:space-between;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;font-size:19px;letter-spacing:2px;text-transform:uppercase;color:#555;padding:12px 0;border-bottom:1px solid #ccc}}
.kick{{font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;font-size:24px;font-weight:bold;letter-spacing:5px;text-transform:uppercase;color:#b5121b;margin:28px 0 12px}}
.hed{{font-size:{hsize}px;line-height:1.05;font-weight:bold;letter-spacing:-1px}}
.deck{{font-size:29px;line-height:1.35;color:#333;margin-top:16px;font-style:italic}}
.photo{{margin-top:24px;flex:1;min-height:300px;background:{'#f4f1ea' if cut else '#ddd'} url('{photo}') center {'center/contain no-repeat' if cut else '60%/cover'}}}
.cred{{font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;font-size:16px;color:#666;margin:8px 0 18px;text-align:right;min-height:18px}}
.foot{{position:absolute;left:0;right:0;bottom:0;height:78px;background:#111;color:#fff;display:flex;align-items:center;justify-content:space-between;padding:0 56px;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif}}
.foot b{{font-size:26px;letter-spacing:1px}}.foot i{{font-style:normal;font-size:22px;color:#e8c9cb;letter-spacing:2px;text-transform:uppercase}}
</style></head><body><div class="wrap">
<div class="mast"><h1>The <span>Vermilion</span> Times</h1><div class="tag">Starbase Louisiana&rsquo;s Local News</div></div>
<div class="date"><span>Vermilion Parish, Louisiana</span><span>{e(date)}</span></div>
<div class="kick">&#9679; {e(a.kicker)}</div>
<div class="hed">{e(a.headline)}</div>
<div class="deck">{e(a.deck)}</div>
<div class="photo"></div>
<div class="cred">{e(a.credit)}</div>
</div><div class="foot"><b>thevermiliontimes.com</b><i>Read the full story</i></div></body></html>"""
os.makedirs(os.path.join(ROOT, 'img', 'social'), exist_ok=True)
out = os.path.join(ROOT, 'img', 'social', a.slug + '.png')
with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False) as f:
    f.write(page); src = f.name
js = f"""const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch({{executablePath:{json.dumps(CHROME)}}});
const p=await b.newPage({{viewport:{{width:1080,height:1350}}}});await p.goto('file://{src}');await p.waitForTimeout(400);
await p.screenshot({{path:{json.dumps(out)}}});await b.close()}})()"""
subprocess.run(['node', '-e', js], check=True, cwd='/tmp')
print(os.path.relpath(out, ROOT))
