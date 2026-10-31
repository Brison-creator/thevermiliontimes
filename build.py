#!/usr/bin/env python3
"""Builds The Vermilion Times: every page, the article pages, the news index,
the RSS feed and the sitemap. Run it after adding or editing a story:

    python3 build.py
"""
import io, os, re, json, glob, html, datetime
from zoneinfo import ZoneInfo
CT=ZoneInfo('America/Chicago')
R=os.path.dirname(os.path.abspath(__file__))+'/'
SITE='https://thevermiliontimes.com'
EMAIL='news@thevermiliontimes.com'
TAGLINE='Starbase Louisiana&rsquo;s Local News'  # the official tagline, everywhere
FONTS='https://fonts.googleapis.com/css2?family=Libre+Caslon+Text:wght@400;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&family=Inter:wght@500;600;700&display=swap'
ICON=("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='10' fill='%23f3e9d4'/%3E"
      "%3Ctext x='32' y='47' font-family='UnifrakturMaguntia,serif' font-size='44' text-anchor='middle' fill='%237c1f1a'%3EV%3C/text%3E%3C/svg%3E")

SECTIONS=[('local','Local'),('government','Parish Government'),('safety','Public Safety'),('schools','Schools'),('sports','Sports'),('business','Business'),
          ('starbase','Starbase Louisiana'),('land-water','Land &amp; Water'),('faith','Faith &amp; Family'),('opinion','Opinion'),('obituaries','Obituaries')]

# ---------------------------------------------------------------- articles
# One story per file in articles/, named YYYY-MM-DD-slug.md:
#
#   ---
#   title: Headline in Title Case
#   deck: One-sentence summary under the headline.
#   section: government        (one of the SECTIONS keys)
#   date: 2026-10-31
#   updated: 2026-11-01        (optional)
#   disclosure: ...            (optional; required when a story touches the publisher's businesses)
#   sources:
#   - Name of source | https://example.com/page
#   ---
#   Body. Blank lines split paragraphs. "## " starts a subhead, "- " a list
#   item, "> " a quotation. Inline: **bold**, *italic*, [text](https://url).
MONTHS=['Jan.','Feb.','March','April','May','June','July','Aug.','Sept.','Oct.','Nov.','Dec.']
def ap_date(d): return f'{MONTHS[d.month-1]} {d.day}, {d.year}'
def ap_time(t):
    h=t.hour%12 or 12; m=f':{t.minute:02d}' if t.minute else ''
    return f'{h}{m} {"a.m." if t.hour<12 else "p.m."}'
def stamp(a,long=False):
    # Blue timestamp; times.js turns fresh ones into "2 hours ago" and adds the New tag.
    label=ap_date(a['d'])+(f', {ap_time(a["pub"])}' if long and a.get('has_time') else '')
    return f'<time class="ts" datetime="{a["pub"].isoformat()}" data-pub="{a["pub"].isoformat()}">{label}</time>'
SECTION_NAME=dict(SECTIONS)

def smart(t):
    # typographic quotes and apostrophes, leaving URLs alone
    parts=re.split(r'(\]\(https?://[^)\s]+\)|https?://\S+)',t)
    for i in range(0,len(parts),2):
        x=parts[i]
        x=re.sub(r'(^|[\s(\[\u2014-])"',lambda m:m.group(1)+'\u201c',x)
        x=x.replace('"','\u201d')
        x=re.sub(r"(^|[\s(\[\u2014-])'",lambda m:m.group(1)+'\u2018',x)
        x=x.replace("'",'\u2019')
        parts[i]=x
    return ''.join(parts)

def inline(t):
    t=html.escape(t,quote=False)
    t=re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)',lambda m:f'<a href="{m.group(2)}" rel="noopener">{m.group(1)}</a>',t)
    t=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',t)
    t=re.sub(r'(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])',r'<em>\1</em>',t)
    return t

def render_body(md):
    out=[]; first=True
    for block in re.split(r'\n\s*\n',md.strip()):
        lines=[l.rstrip() for l in block.strip().split('\n')]
        if lines[0].startswith('## '):
            out.append(f'<h2>{inline(lines[0][3:])}</h2>'); continue
        if all(l.startswith('- ') for l in lines):
            out.append('<ul>'+''.join(f'<li>{inline(l[2:])}</li>' for l in lines)+'</ul>'); continue
        if all(l.startswith('>') for l in lines):
            out.append('<blockquote><p>'+inline(' '.join(l.lstrip('> ').strip() for l in lines))+'</p></blockquote>'); continue
        cls=' class="dropcap"' if first else ''; first=False
        out.append(f'<p{cls}>{inline(" ".join(lines))}</p>')
    return '\n'.join(out)

def load_articles():
    arts=[]
    for f in sorted(glob.glob(os.path.join(R,'articles','*.md'))):
        raw=io.open(f,encoding='utf-8').read()
        m=re.match(r'---\n(.*?)\n---\n(.*)',raw,re.S)
        if not m: raise SystemExit(f'{f}: missing front matter')
        meta={'sources':[]}; key=None
        for line in m.group(1).split('\n'):
            if line.startswith('- ') and key=='sources':
                name,_,url=line[2:].partition('|'); meta['sources'].append((name.strip(),url.strip())); continue
            k,_,v=line.partition(':'); key=k.strip(); v=v.strip()
            if len(v)>1 and v[0]==v[-1] and v[0] in '"\'': v=v[1:-1]  # allow quoted values
            if key!='sources': meta[key]=v
        for need in ('title','deck','section','date'):
            if not meta.get(need): raise SystemExit(f'{f}: missing {need}')
        if meta['section'] not in SECTION_NAME: raise SystemExit(f'{f}: unknown section {meta["section"]}')
        if not meta['sources']: raise SystemExit(f'{f}: every story needs at least one source')
        for k in ('title','deck','disclosure'):
            if meta.get(k): meta[k]=smart(meta[k])
        slug=os.path.basename(f)[11:-3]
        d=datetime.date.fromisoformat(meta['date'])
        hh,mm=(int(x) for x in (meta.get('time') or '06:00').split(':'))
        pub=datetime.datetime(d.year,d.month,d.day,hh,mm,tzinfo=CT)
        body=smart(m.group(2))
        first_para=next(b for b in re.split(r'\n\s*\n',body.strip()) if not b.startswith(('## ','- ','>')))
        arts.append(dict(meta, slug=slug, d=d, pub=pub, has_time=bool(meta.get('time')), upd=datetime.date.fromisoformat(meta['updated']) if meta.get('updated') else None,
                         url=f'/news/{slug}/', body_html=render_body(body),
                         excerpt=re.sub(r'<[^>]+>','',inline(' '.join(first_para.split())))))
    arts.sort(key=lambda a:(a['pub'],a['slug']),reverse=True)
    return arts

ARTICLES=load_articles()
UPDATED=(f'<span class="updated">Updated <time class="ts-abs" datetime="{ARTICLES[0]["pub"].isoformat()}">{MONTHS[ARTICLES[0]["d"].month-1]} {ARTICLES[0]["d"].day}, {ap_time(ARTICLES[0]["pub"])}</time></span>' if ARTICLES else '')

# ---------------------------------------------------------------- images
# A story may carry a freely licensed photo (see tools/commons.py):
#   image: /img/photos/slug.jpg   image_alt: ...   image_caption: ...
#   image_credit: Author / Wikimedia Commons, CC BY 2.0   image_source: https://commons...
# Without one it shows its section's engraving from img/cuts/ (or `illustration: <name>`).
# img/photos/pool.json: real file photos per section (each with image, alt, caption, credit, source)
try: POOL=json.load(io.open(os.path.join(R,'img','photos','pool.json'),encoding='utf-8'))
except OSError: POOL={}
def cut_title(name):
    try: return re.search(r'<title>(.*?)</title>',io.open(os.path.join(R,'img','cuts',name+'.svg'),encoding='utf-8').read()).group(1)
    except (OSError,AttributeError): return ''
for a in ARTICLES:
    if a.get('image'):
        if not os.path.exists(R+a['image'].lstrip('/')): raise SystemExit(f'{a["slug"]}: image {a["image"]} not found')
        for need in ('image_alt','image_credit'):
            if not a.get(need): raise SystemExit(f'{a["slug"]}: a photo needs {need}')
        a['img']=a['image']; a['img_share']=a['image']; a['img_alt']=a['image_alt']
        a['img_caption']=smart(a.get('image_caption',''))
        cred=html.escape(a['image_credit'])
        a['img_credit']=f'<a href="{html.escape(a["image_source"])}" rel="noopener">{cred}</a>' if a.get('image_source') else cred
    elif POOL.get(a.get('illustration') or a['section']) or POOL.get('local'):
        # a real file photo from the section's pool, picked steadily by slug
        pool=POOL.get(a.get('illustration') or a['section']) or POOL['local']
        ph=pool[sum(map(ord,a['slug']))%len(pool)]
        a['img']=ph['image']; a['img_share']=ph['image']; a['img_alt']=ph['alt']
        a['img_caption']='File photo: '+smart(ph['caption'])
        cred=html.escape(ph['credit'])
        a['img_credit']=f'<a href="{html.escape(ph["source"])}" rel="noopener">{cred}</a>'
    else:
        name=a.get('illustration') or a['section']
        if not os.path.exists(os.path.join(R,'img','cuts',name+'.svg')): name='local'
        a['img']=f'/img/cuts/{name}.svg'; a['img_share']=f'/img/cuts/{name}.png'
        a['img_alt']=cut_title(name); a['img_caption']=''; a['img_credit']='Illustration: The Vermilion Times'

def img_size(path):
    # width and height of a JPEG or PNG, so pages reserve the right space
    f=io.open(R+path.lstrip('/'),'rb'); d=f.read(); f.close()
    if d[:8]==b'\x89PNG\r\n\x1a\n': return int.from_bytes(d[16:20],'big'),int.from_bytes(d[20:24],'big')
    i=2
    while i<len(d):
        if d[i]!=0xFF: i+=1; continue
        m=d[i+1]
        if m in (0xC0,0xC1,0xC2): return int.from_bytes(d[i+7:i+9],'big'),int.from_bytes(d[i+5:i+7],'big')
        i+=2+int.from_bytes(d[i+2:i+4],'big')
    return 640,400

def figure(a,cls='story-art',w=None,h=None,lazy=True,caption=True):
    if w is None: w,h=img_size(a['img']) if a['img'].endswith(('.jpg','.jpeg','.png')) else (640,400)
    cap=''
    if caption:
        cap=f'<figcaption>{inline(a["img_caption"])} <span class="credit">{a["img_credit"]}</span></figcaption>'
    load=' loading="lazy"' if lazy else ''
    return f'<figure class="{cls}"><img src="{a["img"]}" alt="{html.escape(a["img_alt"])}" width="{w}" height="{h}"{load} decoding="async">{cap}</figure>'
def latest_in(sec): return next((a for a in ARTICLES if a['section']==sec),None)

def article_body(a):
    def src_item(n,u):
        if not u: return f'<li>{html.escape(n)}</li>'
        host=u.split('//',1)[-1].split('/',1)[0]
        return f'<li>{html.escape(n)} &mdash; <a href="{html.escape(u)}" rel="noopener">{html.escape(host)}</a></li>'
    src=''.join(src_item(n,u) for n,u in a['sources'])
    upd=f' &middot; Updated <time datetime="{a["upd"]}">{ap_date(a["upd"])}</time>' if a['upd'] else ''
    disc=f'<p class="disclose">{inline(a["disclosure"])}</p>' if a.get('disclosure') else ''
    more=''.join([f'<li><a href="{o["url"]}">{html.escape(o["title"])}</a> <span class="meta">{stamp(o)}</span></li>' for o in ARTICLES if o is not a][:5])
    more_html=f'<section class="more"><h2>More From the Times</h2><ul>{more}</ul></section>' if more else ''
    return f'''<article class="page article">
  <p class="kicker"><a href="/news/#{a["section"]}">{SECTION_NAME[a["section"]]}</a></p>
  <h1>{html.escape(a["title"])}</h1>
  <p class="deck">{inline(a["deck"])}</p>
  <p class="byline">By The Vermilion Times &middot; {stamp(a,True)}{upd}</p>
  {figure(a,lazy=False)}
  <div class="article-body">
{a["body_html"]}
  </div>
  {disc}
  <aside class="sources" aria-labelledby="src-h"><h2 id="src-h">Sources</h2><p>This report was compiled from the public sources below.</p><ul>{src}</ul></aside>
  {BRIEF}
  <p class="corrections">See an error? Email <a href="mailto:{EMAIL}?subject=Correction:%20{html.escape(a["slug"])}">{EMAIL}</a> and we will correct it.</p>
  {more_html}
</article>'''

def article_ld(a):
    return {"@context":"https://schema.org","@type":"NewsArticle","headline":a['title'][:110],"description":a['deck'],
            "datePublished":a['pub'].isoformat(),"dateModified":str(a['upd']) if a['upd'] else a['pub'].isoformat(),"articleSection":re.sub('&amp;','&',SECTION_NAME[a['section']]),
            "mainEntityOfPage":SITE+a['url'],"isAccessibleForFree":True,"image":[SITE+a['img_share']],
            "author":{"@type":"Organization","name":"The Vermilion Times","url":SITE+"/"},
            "publisher":{"@type":"NewsMediaOrganization","name":"The Vermilion Times","url":SITE+"/"}}

def news_index_body():
    if not ARTICLES:
        return '<article class="page"><p class="kicker">The News</p><h1>Latest News</h1><p class="deck">The first stories are on their way.</p></article>'
    rows=''.join(f'''<li id="{a["slug"]}"><a href="{a["url"]}" tabindex="-1" aria-hidden="true" class="art-link">{figure(a,'thumb-art',caption=False)}</a><p class="kicker">{SECTION_NAME[a["section"]]}</p><h2 class="h-1"><a href="{a["url"]}">{html.escape(a["title"])}</a></h2>
      <p class="summary">{inline(a["deck"])}</p><p class="meta">{stamp(a)}</p></li>''' for a in ARTICLES)
    anchors=''.join(f'<span id="{k}"></span>' for k,_ in SECTIONS)
    return f'<article class="page news-index">{anchors}<p class="kicker">The News</p><h1>Latest News</h1><p class="deck">Every story in The Vermilion Times, newest first.</p><ol class="news-list">{rows}</ol></article>'


def page(path,title,desc,body,h1_is_plate=False,ld=None,image='/img/og-nameplate.png'):
    cur_attr=' aria-current="page"'
    NAV=[('/news/','Latest Stories'),('/starbase/','Starbase'),('/government/','Government'),('/safety/','Public Safety'),('/business/','Business'),('/sports/','Sports'),('/schools/','Schools'),('/local/','Community'),('/opinion/','Opinion')]
    secnav=''.join(f'<li><a href="{h}"{cur_attr if path==h else ""}>{t}</a></li>' for h,t in NAV)
    np='The <span class="red">Vermilion</span> Times'
    plate=(f'<h1 class="nameplate"><a href="/">{np}</a></h1>' if h1_is_plate
           else f'<p class="nameplate"><a href="/">{np}</a></p>')
    lds=''.join(f'<script type="application/ld+json">\n{json.dumps(o,indent=1,ensure_ascii=True)}\n</script>\n' for o in (ld or []))
    def li(h,t):
        cur=' aria-current="page"' if h==path else ''
        return f'<li><a href="{h}"{cur}>{t}</a></li>'
    news=''.join(li(f'/{k}/',t) for k,t in SECTIONS[:7])
    life=''.join(li(f'/{k}/',t) for k,t in SECTIONS[7:])
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{SITE}{path}">
<meta name="theme-color" content="#000000">
<meta property="og:type" content="website">
<meta property="og:site_name" content="The Vermilion Times">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:image" content="{SITE}{image}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" sizes="32x32" href="/img/brand/icon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="/img/brand/icon-192.png">
<link rel="apple-touch-icon" href="/img/brand/icon-180.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="/assets/times.css">
{lds}</head>
<body>
<a class="skip" href="#main">Skip to the news</a>
<div class="topbar"><div class="wrap topbar-in">
  <p class="tb-left"><span>{TAGLINE}</span><span class="tb-sep" aria-hidden="true">|</span><span id="today">Vermilion Parish, Louisiana</span></p>
  <nav class="tb-right" aria-label="Utility"><a href="/about/">About Us</a><a href="/#brief">Subscribe</a><a href="/about/#contact">Contact</a></nav>
</div></div>
<header class="wrap mast">
  {plate}
  <p class="motto">{TAGLINE}</p>
</header>
<nav class="secnav" aria-label="Sections"><div class="wrap secnav-in">
  <ul>{secnav}</ul>
  <a class="search-btn" href="/search/" aria-label="Search the Times"><svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M15.5 15.5 21 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></a>
</div></nav>
<main id="main" class="wrap">
{body}
</main>
<footer class="site-foot">
  <div class="wrap">
    <div class="si-cols">
      <nav aria-label="News sections"><h3>News</h3><ul>{news}</ul></nav>
      <nav aria-label="Life sections"><h3>Life &amp; Opinion</h3><ul>{life}</ul></nav>
      <nav aria-label="Contribute"><h3>Contribute</h3><ul>{li('/send-news/','Send a Tip')}{li('/send-news/#announcements','Announcements')}{li('/send-news/#letters','Letters to the Editor')}{li('/send-news/#write','Write for the Times')}</ul></nav>
      <nav aria-label="Business"><h3>Business</h3><ul>{li('/send-news/#advertise','Advertise')}{li('/send-news/#advertise','Classifieds')}{li('/send-news/#advertise','Public Notices')}</ul></nav>
      <nav aria-label="About"><h3>The Times</h3><ul>{li('/about/','About Us')}{li('/about/#standards','Our Standards')}{li('/about/#corrections','Corrections')}{li('/about/#press','Press &amp; Credentials')}{li('/about/#contact','Contact')}</ul></nav>
    </div>
  </div>
  <div class="foot-bar"><div class="wrap foot-bar-in">
    <img class="foot-mark" src="/img/brand/icon-192.png" width="40" height="40" alt="" loading="lazy">
    <p>The Vermilion Times is an independent newsroom serving Vermilion Parish and the communities around Starbase Louisiana. Published by Brison McPhail &middot; <a href="mailto:{EMAIL}">{EMAIL}</a></p>
    <nav class="foot-links" aria-label="Legal"><a href="/about/#standards">Standards</a><a href="/about/#corrections">Corrections</a><span>&copy; <span id="year">2026</span> The Vermilion Times</span></nav>
  </div></div>
</footer>
<script src="/assets/times.js" defer></script>
</body>
</html>
'''

TOWNS=' <span class="fleur" aria-hidden="true">&#x269C;</span> '.join(['Abbeville','Kaplan','Erath','Gueydan','Delcambre','Maurice','Perry','Meaux','Henry','Forked Island','Pecan Island','Intracoastal City'])

CARDS=[
 ('local','Local','Abbeville to the Gulf','The towns, the roads, the new businesses and the people of every community in the parish.'),
 ('government','Parish Government','Police Jury &amp; Courthouse','Police Jury, city councils and the school board: what was decided, what it costs and who voted how.'),
 ('safety','Public Safety','Sheriff, Police &amp; Courts','Arrests and charges from official releases, wrecks, fires and the courts, reported carefully and fairly.'),
 ('schools','Schools','Honor Rolls &amp; Graduations','Classrooms, teachers, awards and every honor roll the schools send us.'),
 ('sports','Sports','Friday Nights &amp; Beyond','Scores, standings and the athletes from Kaplan, Abbeville, Erath, Gueydan and North Vermilion.'),
 ('business','Business','Open for Business','Openings, closings, hiring and the people building things here.'),
 ('starbase','Starbase Louisiana','The Launch Site at Pecan Island','What the announced launch site means for jobs, roads, housing and the coast, reported plainly so readers can decide for themselves.'),
 ('land-water','Land &amp; Water','Rice, Crawfish &amp; Cattle','Harvests and prices, the marsh and the coast, hunting and fishing seasons, and the weather that rules all of it.'),
 ('faith','Faith &amp; Family','Churches, Festivals &amp; Fish Fries','Church news, festivals, club meetings, births, weddings and anniversaries.'),
]
def card(k,label,head,txt,extra=''):
    a=latest_in(k)
    status=(f'<p class="card-latest"><span class="meta">Latest &middot; {stamp(a)}</span><a href="{a["url"]}">{html.escape(a["title"])}</a></p>'
            if a else '<span class="status">Coming Soon</span>')
    return f'''<article id="{k}">
      <p class="kicker"><a href="/{k}/">{label}</a></p>
      <h3 class="h-2"><a href="/{k}/">{head}</a></h3>
      <p>{txt}</p>{extra}
      {status}
    </article>'''
DISCLOSE='\n      <p class="disclose">Disclosure: Brison McPhail, publisher of the Times, also owns Rocket Farm, an RV park in Kaplan. Any story that touches it will say so.</p>'
GRID=''.join(card(*c, DISCLOSE if c[0]=='starbase' else '') for c in CARDS)

# The Parish Brief signup. Set BRIEF_ACTION to an email service's form URL
# (Buttondown, Mailchimp...) to collect addresses there; until then the button
# opens an email to the Times asking to be added.
BRIEF_ACTION=''
BRIEF=(f'''<div class="box brief" id="brief"><h3 class="h-2">Get the Parish Brief</h3><p>The day's Vermilion Parish news in your inbox every morning. Free.</p>
  <form action="{BRIEF_ACTION}" method="post" target="_blank"><label class="sr" for="brief-email">Email address</label><input id="brief-email" type="email" name="email" required placeholder="you@example.com"><button class="btn" type="submit">Sign Me Up</button></form></div>''' if BRIEF_ACTION else
  f'''<div class="box brief" id="brief"><h3 class="h-2">Get the Parish Brief</h3><p>The day's Vermilion Parish news in your inbox every morning. Free.</p>
  <a class="btn" href="mailto:{EMAIL}?subject=Sign%20me%20up%20for%20the%20Parish%20Brief&amp;body=Please%20add%20this%20address%20to%20The%20Vermilion%20Times%20Parish%20Brief.">Sign Me Up</a></div>''')
SEC_TEXT={k:(head,txt) for k,_,head,txt in CARDS}
SEC_TEXT['opinion']=('Letters, Columns &amp; the Editorial Board','Signed letters from readers, guest columns about the parish and the paper\'s own positions, always labeled as opinion.')
SEC_TEXT['obituaries']=('Remembering Our Neighbors','Obituaries as sent by families and funeral homes, with service details.')
SEC_TITLE={'starbase':'Starbase Louisiana News and Timeline','safety':'Vermilion Parish Crime and Public Safety News','government':'Vermilion Parish Government News',
           'sports':'Vermilion Parish High School Sports','schools':'Vermilion Parish Schools News','local':'Vermilion Parish Local News'}
def story_list(arts):
    return ''.join(f'''<li id="{a["slug"]}"><a href="{a["url"]}" tabindex="-1" aria-hidden="true" class="art-link">{figure(a,'thumb-art',caption=False)}</a><p class="kicker">{SECTION_NAME[a["section"]]}<span class="new-tag" data-pub="{a["pub"].isoformat()}" hidden>New</span></p><h2 class="h-1"><a href="{a["url"]}">{html.escape(a["title"])}</a></h2>
      <p class="summary">{inline(a["deck"])}</p><p class="meta">{stamp(a)}</p></li>''' for a in arts)
def section_body(k):
    head,txt=SEC_TEXT.get(k,('',''))
    intro=''
    f=os.path.join(R,'sections',k+'.md')
    if os.path.exists(f):
        intro='<div class="section-intro article-body">'+render_body(smart(io.open(f,encoding='utf-8').read())).replace(' class="dropcap"','',1)+'</div>'
    arts=[a for a in ARTICLES if a['section']==k]
    lst=(f'<h2 class="list-head">Latest {SECTION_NAME[k]} Stories</h2><ol class="news-list">{story_list(arts)}</ol>' if arts else
         f'<p class="empty">No stories in this section yet. Know something we should report? <a href="/send-news/">Send us the news from your town</a>.</p>')
    disc=DISCLOSE if k=='starbase' else ''
    return f'''<article class="page section-page"><p class="kicker">{SECTION_NAME[k]}</p><h1>{head}</h1><p class="deck">{txt}</p>{disc}
  {intro}
  {lst}
  {BRIEF}
</article>'''

def pick_featured():
    pinned=[a for a in ARTICLES if a.get('featured','').lower() in ('yes','true','1')]
    return pinned[0] if pinned else ARTICLES[0]
def rail_item(a):
    return f'''<li><p class="kicker">{SECTION_NAME[a["section"]]}<span class="new-tag" data-pub="{a["pub"].isoformat()}" hidden>New</span></p>
      <h3 class="rail-head"><a href="{a["url"]}">{html.escape(a["title"])}</a></h3><p class="meta">{stamp(a)}</p></li>'''
def top_item(a):
    return f'''<article class="ts-item"><a class="ts-img art-link" href="{a["url"]}" tabindex="-1" aria-hidden="true">{figure(a,'thumb-art',caption=False)}</a>
      <div><p class="kicker">{SECTION_NAME[a["section"]]}<span class="new-tag" data-pub="{a["pub"].isoformat()}" hidden>New</span></p>
      <h3 class="ts-head"><a href="{a["url"]}">{html.escape(a["title"])}</a></h3><p class="ts-dek">{inline(a["deck"])}</p><p class="meta">{stamp(a)}</p></div></article>'''
def home_body_html():
    if not ARTICLES:
        return '<p class="empty">The first stories are on their way.</p>'
    feat=pick_featured(); rest=[a for a in ARTICLES if a is not feat]
    rail=rest[:3]; top=rest[3:6]
    TOPS=(f'<section class="top-stories" aria-labelledby="top-h"><h2 id="top-h" class="label">More Top Stories</h2><div class="ts-grid">'+''.join(top_item(a) for a in top)+'</div></section>') if top else ''
    return f'''<div class="front">
  <section class="featured" aria-labelledby="feat-h">
    <div class="feat-text">
      <p class="label">Featured</p>
      <h2 id="feat-h" class="h-lead"><a href="{feat["url"]}">{html.escape(feat["title"])}</a></h2>
      <p class="deck">{inline(feat["deck"])}</p>
      <p class="byline">By The Vermilion Times <span class="sep">|</span> {stamp(feat,True)}</p>
      <a class="more-link" href="{feat["url"]}">Read Full Story <span aria-hidden="true">&rarr;</span></a>
    </div>
    <a class="feat-img art-link" href="{feat["url"]}" tabindex="-1" aria-hidden="true">{figure(feat,'lead-art',lazy=False,caption=False)}</a>
  </section>
  <aside class="latest" aria-labelledby="latest-h">
    <h2 id="latest-h" class="label">Latest Stories</h2>
    <ol class="latest-list">{''.join(rail_item(a) for a in rail)}</ol>
    <a class="more-link" href="/news/">More Stories <span aria-hidden="true">&rarr;</span></a>
  </aside>
</div>
{TOPS}
<section class="watch-band" aria-labelledby="watch-h">
  <div>
    <p class="label">Starbase Watch</p>
    <h2 id="watch-h" class="h-1"><a href="/starbase/">The timeline, the money and the open questions on SpaceX&rsquo;s Louisiana launch site</a></h2>
    <p>Every decision, number and unanswered question about Starbase Louisiana at Pecan Island, sourced and kept up to date.</p>
    <a class="more-link" href="/starbase/">Open Starbase Watch <span aria-hidden="true">&rarr;</span></a>
  </div>
  {BRIEF}
</section>
<section class="sections-band" aria-labelledby="sections-h">
  <h2 id="sections-h" class="label">Sections</h2>
  <div class="grid4">{GRID}</div>
</section>
<section class="help-band" aria-labelledby="help-h">
  <h2 id="help-h" class="label">Be Part of the Paper</h2>
  <div class="grid3">
    <article><h3 class="h-2"><a href="/send-news/">Send a Tip</a></h3><p>Know something the parish should know? We read everything, and we will ask before we name you.</p></article>
    <article><h3 class="h-2"><a href="/send-news/#write">Write for the Times</a></h3><p>We want a correspondent in every town: meetings, scores, openings and the people behind them.</p></article>
    <article><h3 class="h-2"><a href="/send-news/#advertise">Advertise</a></h3><p>Reach Vermilion Parish readers with display ads, classifieds and announcements.</p></article>
  </div>
</section>'''
RECENT=''.join(f'<li><a href="{a["url"]}">{html.escape(a["title"])}</a> <span class="meta">{stamp(a)}</span></li>' for a in ARTICLES[:8])
about_body=f'''<article class="page">
  <p class="kicker">About the Times</p>
  <h1>Of the Parish, for the Parish</h1>
  <p class="deck">The Vermilion Times is an independent digital news outlet covering Vermilion Parish, Louisiana, and Starbase Louisiana: {TAGLINE}.</p>
  <p class="dropcap">We started this paper because Vermilion Parish deserves steady, local coverage: of its government, its schools, its businesses and its people. We are independent and locally owned, and we answer to our readers.</p>
  <h2>What We Cover</h2>
  <p>Local government and public meetings, schools and sports, business, faith and community life, agriculture and the coast, and the changes coming to the parish, including the announced Starbase Louisiana launch site at Pecan Island.</p>
  <h2 id="standards">Our Standards</h2>
  <ul>
    <li><b>Accuracy first.</b> We check what we print, and we name our sources whenever we can.</li>
    <li id="corrections"><b>Corrections.</b> When we get something wrong, we fix it promptly and say so plainly. Send corrections to <a href="mailto:{EMAIL}">{EMAIL}</a>.</li>
    <li><b>News and opinion are kept apart.</b> Opinion is always labeled as opinion.</li>
    <li><b>Conflicts are disclosed.</b> When we report on a business or organization connected to the paper&rsquo;s publisher, Brison McPhail, including Rocket Farm, his RV park in Kaplan, we say so in the story.</li>
    <li><b>Advertising does not buy coverage.</b> Advertisers do not decide what we report.</li>
  </ul>
  <h2 id="publisher">The Publisher</h2>
  <p class="with-photo"><img class="pub-photo" src="/img/publisher.png" width="56" height="56" alt="Brison McPhail"><span>The Vermilion Times is published by Brison McPhail. He also owns Rocket Farm, an RV park in development in Kaplan; the Times discloses that connection in every story about Starbase Louisiana or anything touching his businesses.</span></p>
  <h2 id="press">Newsroom &amp; Press</h2>
  <ul>
    <li><b>Outlet:</b> The Vermilion Times, an independent digital news outlet, established 2026.</li>
    <li><b>Coverage:</b> Vermilion Parish government, public safety, schools, sports, business, the coast, and SpaceX&rsquo;s Starbase Louisiana launch site at Pecan Island.</li>
    <li><b>Publisher:</b> Brison McPhail.</li>
    <li><b>Disclosure:</b> The publisher also owns Rocket Farm, an RV park in development in Kaplan; every Starbase Louisiana story says so.</li>
    <li><b>Press and credential requests:</b> <a href="mailto:{EMAIL}?subject=Press%20inquiry">{EMAIL}</a>.</li>
    <li><b>Publishing schedule:</b> new stories daily, each dated and sourced.</li>
  </ul>
  <h3 class="h-2">Recent Stories</h3>
  <ul class="recent">{RECENT}</ul>
  <h2 id="contact">Contact</h2>
  <p>News, letters, corrections and advertising: <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
</article>'''

send_body=f'''<article class="page">
  <p class="kicker">Send Us News</p>
  <h1>Tell the Parish</h1>
  <p class="deck">The best stories come from the people who live them. Here is how to get yours into the Times.</p>
  <h2 id="news">News &amp; Tips</h2>
  <p class="dropcap">Email <a href="mailto:{EMAIL}">{EMAIL}</a> with what happened, where and when, who was involved, and how we can reach you. Photos are welcome; tell us who took them and who is in them.</p>
  <p>If you want to share something in confidence, say so at the top of your message before you give details.</p>
  <h2 id="announcements">Announcements</h2>
  <ul>
    <li><b>Births, weddings and anniversaries:</b> names, dates, towns and a photo if you have one.</li>
    <li><b>Obituaries:</b> sent by the family or the funeral home, with service details.</li>
    <li><b>School news:</b> honor rolls, awards, graduations and scores, from the school or coach.</li>
    <li><b>Church, club and festival news:</b> the event, the date, the place and a contact.</li>
  </ul>
  <h2 id="letters">Letters &amp; Columns</h2>
  <p>Letters to the editor should be signed with your name and town; we print them as written, trimmed only for length. Guest columns about the parish are welcome too: send a short pitch first.</p>
  <h2 id="write">Write for the Times</h2>
  <p>We want correspondents in every town in the parish. Email us with your name, your town, what you would like to cover and, if you have one, something you have written.</p>
  <h2 id="advertise">Advertise</h2>
  <p>Display ads, classifieds and business announcements. Email <a href="mailto:{EMAIL}">{EMAIL}</a> with your business name and what you would like to run, and we will send rates and sizes. Charter advertisers who sign on before the first edition get first pick of placement.</p>
</article>'''

nf_body='''<article class="page" style="text-align:center">
  <p class="kicker">Page Not Found</p>
  <h1>This Page Has Gone to Press Elsewhere</h1>
  <p class="deck">The page you were looking for is not in this edition.</p>
  <p><a href="/">Return to the Front Page &rarr;</a></p>
</article>'''

org={"@context":"https://schema.org","@type":"NewsMediaOrganization","name":"The Vermilion Times","url":SITE+"/",
     "slogan":"Starbase Louisiana\u2019s Local News","email":EMAIL,"logo":SITE+"/img/brand/round-720.png","foundingDate":"2026","founder":{"@type":"Person","name":"Brison McPhail","jobTitle":"Publisher"},"areaServed":{"@type":"AdministrativeArea","name":"Vermilion Parish, Louisiana"},
     "publishingPrinciples":SITE+"/about/","correctionsPolicy":SITE+"/about/","ethicsPolicy":SITE+"/about/"}
files={
 'index.html':page('/','The Vermilion Times | Starbase Louisiana&rsquo;s Local News',
   'Starbase Louisiana&rsquo;s Local News: The Vermilion Times covers Vermilion Parish, from SpaceX at Pecan Island to Abbeville, Kaplan, Erath and the coast.',home_body_html(),True,[org]),
 'about/index.html':page('/about/','About the Times | The Vermilion Times',
   'About The Vermilion Times, an independent newspaper for Vermilion Parish, Louisiana: what we cover, our standards, corrections and how to reach us.',about_body),
 'send-news/index.html':page('/send-news/','Send Us News | The Vermilion Times',
   'Send news, tips, announcements and obituaries to The Vermilion Times, write for the paper as a town correspondent, or advertise with us.',send_body),
 '404.html':page('/404.html','Page Not Found | The Vermilion Times','That page is not in this edition of The Vermilion Times.',nf_body),
 'news/index.html':page('/news/','Latest News | The Vermilion Times',
   'The latest news from Vermilion Parish, Louisiana, from The Vermilion Times: government, schools, sports, business, the coast and Starbase Louisiana.',news_index_body()),
}
for k,_ in SECTIONS:
    head,txt=SEC_TEXT.get(k,('',''))
    files[f'{k}/index.html']=page(f'/{k}/',f'{SEC_TITLE.get(k,re.sub("&amp;","&",SECTION_NAME[k])+" News")} | The Vermilion Times'.replace('&','&amp;').replace('&amp;amp;','&amp;'),
        re.sub('<[^>]+>','',txt)[:158],section_body(k),False,None,'/img/cuts/'+(k if os.path.exists(os.path.join(R,'img','cuts',k+'.png')) else 'local')+'.png')
# search: a small JSON index the search page filters in the browser
io.open(R+'search.json','w',encoding='utf-8').write(json.dumps([{'t':re.sub('<[^>]+>','',html.unescape(x['title'])),'d':re.sub('<[^>]+>','',inline(x['deck'])),
    's':re.sub('&amp;','&',SECTION_NAME[x['section']]),'u':x['url'],'p':ap_date(x['d']),'b':re.sub('<[^>]+>',' ',x['body_html'])[:4000]} for x in ARTICLES],ensure_ascii=False))
files['search/index.html']=page('/search/','Search | The Vermilion Times','Search every story in The Vermilion Times, Starbase Louisiana&rsquo;s Local News.','''<article class="page"><p class="kicker">Search</p><h1>Search the Times</h1>
  <form class="search-box" role="search" onsubmit="return false"><label class="sr" for="q">Search stories</label><input id="q" type="search" placeholder="Starbase, Police Jury, Kaplan..." autocomplete="off"></form>
  <p id="search-status" class="meta" aria-live="polite"></p><ol id="results" class="news-list"></ol>
  <noscript><p>Search needs JavaScript. Browse <a href="/news/">every story</a> instead.</p></noscript>
</article>
<script src="/assets/search.js" defer></script>''')
def meta_desc(t):
    t=re.sub(r'<[^>]+>','',t).replace('"','&quot;')
    return t if len(t)<=158 else t[:155].rsplit(' ',1)[0]+'...'
for a in ARTICLES:
    files[a['url'].strip('/')+'/index.html']=page(a['url'],f'{html.escape(a["title"])} | The Vermilion Times',meta_desc(inline(a['deck'])),article_body(a),False,[article_ld(a)],a['img_share'])
# drop pages for stories that were removed
for d in glob.glob(R+'news/*/'):
    if d[len(R):]+'index.html' not in files:
        import shutil; shutil.rmtree(d)
for p,s in files.items():
    os.makedirs(os.path.dirname(R+p) or R,exist_ok=True); io.open(R+p,'w',encoding='utf-8').write(s)
io.open(R+'robots.txt','w').write(f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n')
TODAY=str(ARTICLES[0]['d']) if ARTICLES else '2026-10-30'
urls=[('/',TODAY),('/news/',TODAY)]+[(f'/{k}/',TODAY) for k,_ in SECTIONS]+[('/about/','2026-10-31'),('/send-news/','2026-10-31')]+[(a['url'],str(a['upd'] or a['d'])) for a in ARTICLES]
io.open(R+'sitemap.xml','w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+
  ''.join(f'  <url><loc>{SITE}{u}</loc><lastmod>{d}</lastmod></url>\n' for u,d in urls)+'</urlset>\n')
def rfc822(d): return datetime.datetime(d.year,d.month,d.day,6,0,tzinfo=datetime.timezone(datetime.timedelta(hours=-6))).strftime('%a, %d %b %Y %H:%M:%S %z')
items=''.join(f'''  <item><title>{html.escape(a["title"])}</title><link>{SITE}{a["url"]}</link><guid>{SITE}{a["url"]}</guid><pubDate>{rfc822(a["d"])}</pubDate><category>{html.escape(re.sub("&amp;","&",SECTION_NAME[a["section"]]))}</category><description>{html.escape(re.sub(r"<[^>]+>","",inline(a["deck"])))}</description></item>
''' for a in ARTICLES[:30])
io.open(R+'feed.xml','w',encoding='utf-8').write(f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>The Vermilion Times</title><link>{SITE}/</link><description>Starbase Louisiana's Local News</description><language>en-us</language>
{items}</channel></rss>
''')
for p,s in files.items():
    d=re.search(r'name="description" content="([^"]*)"',s).group(1); t=re.search(r'<title>([^<]*)',s).group(1)
    print(f'{p:22} title {len(t):3} desc {len(d):3}')
