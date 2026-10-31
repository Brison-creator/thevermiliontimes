#!/usr/bin/env python3
"""Builds The Vermilion Times: every page, the article pages, the news index,
the RSS feed and the sitemap. Run it after adding or editing a story:

    python3 build.py
"""
import io, os, re, json, glob, html, datetime
R=os.path.dirname(os.path.abspath(__file__))+'/'
SITE='https://thevermiliontimes.com'
EMAIL='news@thevermiliontimes.com'
FONTS='https://fonts.googleapis.com/css2?family=UnifrakturMaguntia&family=Grenze+Gotisch:wght@700&family=EB+Garamond:ital,wght@0,400;0,600;1,400&family=IM+Fell+English+SC&display=swap'
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
            if key!='sources': meta[key]=v
        for need in ('title','deck','section','date'):
            if not meta.get(need): raise SystemExit(f'{f}: missing {need}')
        if meta['section'] not in SECTION_NAME: raise SystemExit(f'{f}: unknown section {meta["section"]}')
        if not meta['sources']: raise SystemExit(f'{f}: every story needs at least one source')
        for k in ('title','deck','disclosure'):
            if meta.get(k): meta[k]=smart(meta[k])
        slug=os.path.basename(f)[11:-3]
        d=datetime.date.fromisoformat(meta['date'])
        body=smart(m.group(2))
        first_para=next(b for b in re.split(r'\n\s*\n',body.strip()) if not b.startswith(('## ','- ','>')))
        arts.append(dict(meta, slug=slug, d=d, upd=datetime.date.fromisoformat(meta['updated']) if meta.get('updated') else None,
                         url=f'/news/{slug}/', body_html=render_body(body),
                         excerpt=re.sub(r'<[^>]+>','',inline(' '.join(first_para.split())))))
    arts.sort(key=lambda a:(a['d'],a['slug']),reverse=True)
    return arts

ARTICLES=load_articles()

# ---------------------------------------------------------------- images
# A story may carry a freely licensed photo (see tools/commons.py):
#   image: /img/photos/slug.jpg   image_alt: ...   image_caption: ...
#   image_credit: Author / Wikimedia Commons, CC BY 2.0   image_source: https://commons...
# Without one it shows its section's engraving from img/cuts/ (or `illustration: <name>`).
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
    more=''.join([f'<li><a href="{o["url"]}">{html.escape(o["title"])}</a> <span class="meta">{ap_date(o["d"])}</span></li>' for o in ARTICLES if o is not a][:5])
    more_html=f'<section class="more"><h2>More From the Times</h2><ul>{more}</ul></section>' if more else ''
    return f'''<article class="page article">
  <p class="kicker"><a href="/news/#{a["section"]}">{SECTION_NAME[a["section"]]}</a></p>
  <h1>{html.escape(a["title"])}</h1>
  <p class="deck">{inline(a["deck"])}</p>
  <p class="byline">By The Vermilion Times &middot; <time datetime="{a["d"]}">{ap_date(a["d"])}</time>{upd}</p>
  {figure(a,lazy=False)}
  <div class="article-body">
{a["body_html"]}
  </div>
  {disc}
  <aside class="sources" aria-labelledby="src-h"><h2 id="src-h">Sources</h2><p>This report was compiled from the public sources below.</p><ul>{src}</ul></aside>
  <p class="corrections">See an error? Email <a href="mailto:{EMAIL}?subject=Correction:%20{html.escape(a["slug"])}">{EMAIL}</a> and we will correct it.</p>
  {more_html}
</article>'''

def article_ld(a):
    return {"@context":"https://schema.org","@type":"NewsArticle","headline":a['title'][:110],"description":a['deck'],
            "datePublished":str(a['d']),"dateModified":str(a['upd'] or a['d']),"articleSection":re.sub('&amp;','&',SECTION_NAME[a['section']]),
            "mainEntityOfPage":SITE+a['url'],"isAccessibleForFree":True,"image":[SITE+a['img_share']],
            "author":{"@type":"Organization","name":"The Vermilion Times","url":SITE+"/"},
            "publisher":{"@type":"NewsMediaOrganization","name":"The Vermilion Times","url":SITE+"/"}}

def news_index_body():
    if not ARTICLES:
        return '<article class="page"><p class="kicker">The News</p><h1>Latest News</h1><p class="deck">The first stories are on their way.</p></article>'
    rows=''.join(f'''<li id="{a["slug"]}"><a href="{a["url"]}" tabindex="-1" aria-hidden="true" class="art-link">{figure(a,'thumb-art',caption=False)}</a><p class="kicker">{SECTION_NAME[a["section"]]}</p><h2 class="h-1"><a href="{a["url"]}">{html.escape(a["title"])}</a></h2>
      <p class="summary">{inline(a["deck"])}</p><p class="meta">{ap_date(a["d"])}</p></li>''' for a in ARTICLES)
    anchors=''.join(f'<span id="{k}"></span>' for k,_ in SECTIONS)
    return f'<article class="page news-index">{anchors}<p class="kicker">The News</p><h1>Latest News</h1><p class="deck">Every story in The Vermilion Times, newest first.</p><ol class="news-list">{rows}</ol></article>'


def page(path,title,desc,body,h1_is_plate=False,ld=None,image='/img/og-nameplate.png'):
    secnav=''.join(f'<li><a href="/#{k}">{t}</a></li>' for k,t in SECTIONS)
    plate=('<h1 class="nameplate">The Vermilion Times</h1>' if h1_is_plate
           else '<p class="nameplate"><a href="/">The Vermilion Times</a></p>')
    lds=''.join(f'<script type="application/ld+json">\n{json.dumps(o,indent=1,ensure_ascii=True)}\n</script>\n' for o in (ld or []))
    def li(h,t):
        cur=' aria-current="page"' if h==path else ''
        return f'<li><a href="{h}"{cur}>{t}</a></li>'
    news=''.join(li(f'/#{k}',t) for k,t in SECTIONS[:7])
    life=''.join(li(f'/#{k}',t) for k,t in SECTIONS[7:])
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{SITE}{path}">
<meta name="theme-color" content="#f6f2e6">
<meta property="og:type" content="website">
<meta property="og:site_name" content="The Vermilion Times">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:image" content="{SITE}{image}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{ICON}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="/assets/times.css">
{lds}</head>
<body>
<a class="skip" href="#main">Skip to the news</a>
<header class="wrap">
  <div class="topbar">
    <div class="editions"><span><b>Vermilion Parish Edition</b></span><span>Abbeville</span><span>Kaplan</span><span>Erath</span><span>Gueydan</span><span>The Coast</span></div>
    <a class="btn" href="/send-news/">Send a Tip</a>
  </div>
  <div class="masthead">
    <div class="mh-side"><b id="today">Vermilion Parish, Louisiana</b><span class="small">Today&rsquo;s Paper</span></div>
    {plate}
    <div class="mh-side mh-right"><b>Vol. I &middot; No. 1</b><span class="small">Established MMXXVI</span></div>
  </div>
  <p class="motto">&ldquo;All the news of Vermilion Parish, from the prairie to the coast.&rdquo;</p>
  <nav class="secnav" aria-label="Sections"><ul>{secnav}</ul></nav>
</header>
<main id="main" class="wrap">
{body}
</main>
<footer class="wrap siteindex">
  <div class="si-top">
    <p class="si-plate"><a href="/">The Vermilion Times</a></p>
    <a class="btn ghost" href="/send-news/">Send Us News</a>
  </div>
  <h2 class="si-label">Site Index</h2>
  <div class="si-cols">
    <nav aria-label="News sections"><h3>News</h3><ul>{news}</ul></nav>
    <nav aria-label="Life sections"><h3>Life &amp; Opinion</h3><ul>{life}</ul></nav>
    <nav aria-label="Contribute"><h3>Contribute</h3><ul>{li('/send-news/','Send a Tip')}{li('/send-news/#announcements','Announcements')}{li('/send-news/#letters','Letters to the Editor')}{li('/send-news/#write','Write for the Times')}</ul></nav>
    <nav aria-label="Business"><h3>Business</h3><ul>{li('/send-news/#advertise','Advertise')}{li('/send-news/#advertise','Classifieds')}{li('/send-news/#advertise','Public Notices')}</ul></nav>
    <nav aria-label="About"><h3>The Times</h3><ul>{li('/about/','About the Times')}{li('/about/#standards','Our Standards')}{li('/about/#corrections','Corrections')}{li('/about/#contact','Contact')}</ul></nav>
  </div>
  <div class="si-legal">
    <span>&copy; <span id="year">2026</span> The Vermilion Times</span>
    <span>Brison McPhail, Publisher &middot; Published in Vermilion Parish, Louisiana</span>
    <a href="mailto:{EMAIL}">{EMAIL}</a>
  </div>
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
    status=(f'<p class="latest"><span class="meta">Latest &middot; {ap_date(a["d"])}</span><a href="{a["url"]}">{html.escape(a["title"])}</a></p>'
            if a else '<span class="status">Coming Soon</span>')
    return f'''<article id="{k}">
      <p class="kicker">{label}</p>
      <h3 class="h-2">{head}</h3>
      <p>{txt}</p>{extra}
      {status}
    </article>'''
DISCLOSE='\n      <p class="disclose">Disclosure: Brison McPhail, publisher of the Times, also owns Rocket Farm, an RV park in Kaplan. Any story that touches it will say so.</p>'
GRID=''.join(card(*c, DISCLOSE if c[0]=='starbase' else '') for c in CARDS)

def news_block():
    if not ARTICLES: return ''
    lead=ARTICLES[0]; side=ARTICLES[1:4]
    side_html=''.join(f'''<article class="side-story"><a href="{a["url"]}" tabindex="-1" aria-hidden="true" class="art-link">{figure(a,'side-art',caption=False)}</a><p class="kicker">{SECTION_NAME[a["section"]]}</p><h3 class="h-2"><a href="{a["url"]}">{html.escape(a["title"])}</a></h3>
        <p class="summary">{inline(a["deck"])}</p><p class="meta">{ap_date(a["d"])}</p></article>''' for a in side)
    side_col=f'<div class="side-col">{side_html}</div>' if side else ''
    return f'''<div class="story news-lead{' solo' if not side else ''}">
      <article>
        <a href="{lead["url"]}" tabindex="-1" aria-hidden="true" class="art-link">{figure(lead,'lead-art',lazy=False,caption=False)}</a>
        <p class="kicker">{SECTION_NAME[lead["section"]]}</p>
        <h2 class="h-lead"><a href="{lead["url"]}">{html.escape(lead["title"])}</a></h2>
        <p class="summary">{inline(lead["deck"])}</p>
        <p class="excerpt">{html.escape(lead["excerpt"][:420]).rsplit(" ",1)[0] if len(lead["excerpt"])>420 else html.escape(lead["excerpt"])}{"&hellip;" if len(lead["excerpt"])>420 else ""}</p>
        <p class="meta">{ap_date(lead["d"])} &middot; <a class="link" href="{lead["url"]}">Read the story</a></p>
      </article>
      {side_col}
    </div>'''
RIBBON=(f'<p class="ribbon"><span class="tag">Latest</span><span><a href="{ARTICLES[0]["url"]}">{html.escape(ARTICLES[0]["title"])}</a></span></p>' if ARTICLES else
        '<p class="ribbon"><span class="tag">From the Publisher</span><span>The Vermilion Times is getting ready for its first edition. <a href="/send-news/">Send us the news from your town &rarr;</a></span></p>')
home_body=f'''{RIBBON}

<div class="front">
  <div class="well">
    {news_block()}
    <div class="story lead">
      <article>
        <p class="kicker">A Letter From the Publisher</p>
        <h2 class="h-lead"><a href="#letter">A Newspaper for Vermilion Parish Starts Here</a></h2>
        <p class="summary">An independent paper, written for the people who live here and about the things that matter to them.</p>
        <ul class="bullets">
          <li>Police Jury, councils and the school board, covered meeting by meeting.</li>
          <li>Scores, honor rolls, festivals and the people of every town.</li>
          <li>The Starbase Louisiana launch site at Pecan Island, reported plainly.</li>
        </ul>
        <p class="meta">3 min read</p>
      </article>
      <figure>
        <div class="cut"><img src="/img/vermilion-oak.svg" width="640" height="400" alt="Engraving of a live oak hung with moss beside the river at sunrise, a man poling a pirogue across the water"></div>
        <figcaption>Sunrise on the water. Illustration for The Vermilion Times.</figcaption>
      </figure>
    </div>

    <div class="story split">
      <article id="letter">
        <p class="kicker">From the Publisher</p>
        <h2 class="h-1">Every Parish Deserves a Paper That Shows Up</h2>
        <p class="byline with-photo"><img class="pub-photo" src="/img/publisher.png" width="40" height="40" alt="Brison McPhail"><span>By Brison McPhail, Publisher &middot; Vermilion Parish, La.</span></p>
        <p class="dropcap">One that sits through the Police Jury meeting, knows the score of Friday night&rsquo;s game, prints the honor roll, and tells you which new business just opened its doors on Main Street.</p>
        <p>That is what The Vermilion Times sets out to be. We will cover Abbeville and Kaplan, Erath and Gueydan, Delcambre, Maurice and the coast: the councils and the courthouse, the schools and the ball fields, the churches and the festivals, the harvest and the water, and the people who keep it all going.</p>
      </article>
      <article>
        <p class="kicker">The Road Ahead</p>
        <h2 class="h-1">Big Changes Are Coming. We Will Report Them Fairly.</h2>
        <p class="summary">From the announced Starbase Louisiana launch site at Pecan Island to the growth it may bring, the parish has a lot to weigh. We intend to lay out the facts so the people who live here can make up their own minds.</p>
        <p>Our first edition is coming soon. Until then, we want to hear from you: the news, the milestones, the questions nobody is answering. This paper belongs to the parish. Help us fill it.</p>
        <p class="byline">&mdash; Brison McPhail, Publisher</p>
      </article>
    </div>

    <div class="story split">
      <article>
        <p class="kicker">Correspondents Wanted</p>
        <h2 class="h-1"><a href="/send-news/#write">A Correspondent in Every Town</a></h2>
        <p class="summary">We are looking for people who go to the meetings, know the coaches and can write a clean, fair paragraph. Students and retirees welcome.</p>
        <p class="meta">Tell us your town</p>
      </article>
      <article>
        <p class="kicker">Your News</p>
        <h2 class="h-1"><a href="/send-news/">How to Get Your News in the Times</a></h2>
        <ul class="bullets">
          <li>Meetings, decisions and public notices</li>
          <li>Scores, honor rolls and graduations</li>
          <li>Births, weddings and obituaries</li>
          <li>Church, club and festival news</li>
        </ul>
      </article>
    </div>
  </div>

  <aside class="rail" id="opinion" aria-label="Opinion">
    <h2 class="rail-head">Opinion</h2>
    <div class="op">
      <span class="who">The Editorial Board</span>
      <h3 class="h-op"><a href="/about/#standards">What This Paper Promises Its Readers</a></h3>
      <p>Accuracy first. News kept apart from opinion. Conflicts disclosed. Advertising never buys coverage.</p>
    </div>
    <div class="op">
      <span class="who">Letters to the Editor</span>
      <h3 class="h-op"><a href="/send-news/#letters">The First Letters Page Is Yours to Fill</a></h3>
      <p>Agree with us, argue with us, tell the parish what is on your mind. Sign your name and your town.</p>
    </div>
    <div class="op">
      <span class="who">Guest Columns</span>
      <h3 class="h-op"><a href="/send-news/#letters">Have Something to Say About Vermilion?</a></h3>
      <p>Farmers, teachers, pastors, business owners: pitch us a column about the parish you know.</p>
    </div>
    <div class="box">
      <h3 class="h-2">Got a Tip?</h3>
      <p>Know something the parish should know? Tell us. We read everything, and we will ask before we name you.</p>
      <a class="btn" href="mailto:{EMAIL}?subject=News%20tip">Send a Tip</a>
    </div>
    <div class="box">
      <h3 class="h-2">Advertise in the First Edition</h3>
      <p>Charter advertisers who sign on before the first edition get first pick of placement.</p>
      <a class="link" href="/send-news/#advertise">Ask about advertising &rarr;</a>
    </div>
    <div class="op" id="obituaries">
      <span class="who">Obituaries</span>
      <h3 class="h-op"><a href="/send-news/#announcements">Remembering Our Neighbors</a></h3>
      <p>Obituaries are printed as sent by the family or the funeral home, with service details.</p>
    </div>
  </aside>
</div>

<section class="band" aria-labelledby="sections-h">
  <div class="band-head"><h2 id="sections-h">In These Pages</h2><span>Sections of the Times</span></div>
  <div class="grid4">
    {GRID}
  </div>
</section>

<section class="band" aria-labelledby="join-h">
  <div class="band-head"><h2 id="join-h">Be Part of the Paper</h2><span>The Times belongs to the parish</span></div>
  <div class="grid3">
    <article>
      <p class="kicker">Announcements</p>
      <h3 class="h-2">Births, Weddings &amp; Milestones</h3>
      <p>Send names, dates, towns and a photo if you have one. Anniversaries and birthdays welcome.</p>
      <p><a href="/send-news/#announcements">Send an announcement &rarr;</a></p>
    </article>
    <article>
      <p class="kicker">Schools &amp; Coaches</p>
      <h3 class="h-2">Send Us Your Scores</h3>
      <p>Coaches and athletic directors: send results after every game, with the standouts and the stats.</p>
      <p><a href="/send-news/#news">Send scores &rarr;</a></p>
    </article>
    <article>
      <p class="kicker">Local Business</p>
      <h3 class="h-2">Reach Your Neighbors</h3>
      <p>Display ads, classifieds and announcements for businesses across the parish.</p>
      <p><a href="/send-news/#advertise">Advertise with us &rarr;</a></p>
    </article>
  </div>
</section>

<p class="towns">{TOWNS}</p>'''

about_body=f'''<article class="page">
  <p class="kicker">About the Times</p>
  <h1>Of the Parish, for the Parish</h1>
  <p class="deck">The Vermilion Times is an independent local newspaper serving Vermilion Parish, Louisiana.</p>
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
     "email":EMAIL,"logo":SITE+"/img/logo-square.png","foundingDate":"2026","founder":{"@type":"Person","name":"Brison McPhail","jobTitle":"Publisher"},"areaServed":{"@type":"AdministrativeArea","name":"Vermilion Parish, Louisiana"},
     "publishingPrinciples":SITE+"/about/","correctionsPolicy":SITE+"/about/","ethicsPolicy":SITE+"/about/"}
files={
 'index.html':page('/','The Vermilion Times | News for Vermilion Parish, Louisiana',
   'The Vermilion Times: an independent local newspaper for Vermilion Parish, Louisiana, covering Abbeville, Kaplan, Erath, Gueydan, Delcambre and the coast.',home_body,True,[org]),
 'about/index.html':page('/about/','About the Times | The Vermilion Times',
   'About The Vermilion Times, an independent newspaper for Vermilion Parish, Louisiana: what we cover, our standards, corrections and how to reach us.',about_body),
 'send-news/index.html':page('/send-news/','Send Us News | The Vermilion Times',
   'Send news, tips, announcements and obituaries to The Vermilion Times, write for the paper as a town correspondent, or advertise with us.',send_body),
 '404.html':page('/404.html','Page Not Found | The Vermilion Times','That page is not in this edition of The Vermilion Times.',nf_body),
 'news/index.html':page('/news/','Latest News | The Vermilion Times',
   'The latest news from Vermilion Parish, Louisiana, from The Vermilion Times: government, schools, sports, business, the coast and Starbase Louisiana.',news_index_body()),
}
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
urls=[('/',TODAY),('/news/',TODAY),('/about/','2026-10-31'),('/send-news/','2026-10-31')]+[(a['url'],str(a['upd'] or a['d'])) for a in ARTICLES]
io.open(R+'sitemap.xml','w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+
  ''.join(f'  <url><loc>{SITE}{u}</loc><lastmod>{d}</lastmod></url>\n' for u,d in urls)+'</urlset>\n')
def rfc822(d): return datetime.datetime(d.year,d.month,d.day,6,0,tzinfo=datetime.timezone(datetime.timedelta(hours=-6))).strftime('%a, %d %b %Y %H:%M:%S %z')
items=''.join(f'''  <item><title>{html.escape(a["title"])}</title><link>{SITE}{a["url"]}</link><guid>{SITE}{a["url"]}</guid><pubDate>{rfc822(a["d"])}</pubDate><category>{html.escape(re.sub("&amp;","&",SECTION_NAME[a["section"]]))}</category><description>{html.escape(re.sub(r"<[^>]+>","",inline(a["deck"])))}</description></item>
''' for a in ARTICLES[:30])
io.open(R+'feed.xml','w',encoding='utf-8').write(f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>The Vermilion Times</title><link>{SITE}/</link><description>News for Vermilion Parish, Louisiana</description><language>en-us</language>
{items}</channel></rss>
''')
for p,s in files.items():
    d=re.search(r'name="description" content="([^"]*)"',s).group(1); t=re.search(r'<title>([^<]*)',s).group(1)
    print(f'{p:22} title {len(t):3} desc {len(d):3}')
