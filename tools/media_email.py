#!/usr/bin/env python3
"""Build a Vermilion Times media request as newspaper-style HTML email + plain text.

Usage: python3 tools/media_email.py request.json out_prefix
request.json fields:
  greeting       "Hello Mr. LeJeune,"
  intro          one paragraph: who we are / why writing
  about          paragraph(s) for ABOUT THE STORY (string or list)
  ask            the easy ask, e.g. "A brief statement by email is all we need."
  questions      list of strings (optional)
  format, timing, attribution   short paragraphs (optional)
  closing        e.g. "Thank you for your time."
  date           e.g. "Thursday, November 12, 2026"
Writes out_prefix.html and out_prefix.txt. Uses only inline CSS and tables so it
renders the same in Gmail, Outlook and phone mail apps.
"""
import html, json, sys

RED = '#b5121b'; INK = '#111111'; MUTED = '#666666'; RULE = '#d9d9d9'
SERIF = "Georgia, 'Times New Roman', Times, serif"
SANS = "'Helvetica Neue', Helvetica, Arial, sans-serif"
SITE = 'https://thevermiliontimes.com'

def e(s): return html.escape(s, quote=False)

def para(t):
    return (f'<p style="margin:0 0 16px;font-family:{SERIF};font-size:17px;line-height:1.6;color:{INK};">{e(t)}</p>')

def head(t):
    return (f'<p style="margin:26px 0 10px;font-family:{SANS};font-size:11px;font-weight:bold;letter-spacing:2px;'
            f'text-transform:uppercase;color:{RED};border-top:1px solid {RULE};padding-top:14px;">{e(t)}</p>')

def build(r):
    parts = [para(r['greeting']), para(r['intro'])]
    about = r['about'] if isinstance(r['about'], list) else [r['about']]
    parts += [head('About the story')] + [para(a) for a in about]
    parts += [head('What we are asking')]
    parts.append(f'<p style="margin:0 0 16px;font-family:{SERIF};font-size:18px;line-height:1.5;font-style:italic;color:{INK};">{e(r["ask"])}</p>')
    if r.get('questions'):
        lis = ''.join(f'<li style="margin:0 0 10px;font-family:{SERIF};font-size:17px;line-height:1.55;color:{INK};">{e(q)}</li>' for q in r['questions'])
        parts.append(f'<p style="margin:0 0 8px;font-family:{SERIF};font-size:17px;color:{INK};">If helpful, these are the questions our readers are asking:</p>'
                     f'<ol style="margin:0 0 16px;padding-left:22px;">{lis}</ol>')
    for k, label in (('format', 'Format'), ('timing', 'Timing'), ('attribution', 'Attribution')):
        if r.get(k): parts += [head(label), para(r[k])]
    parts.append(para(r.get('closing', 'Thank you for your time.')))
    body = '\n'.join(parts)
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f3ef;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f3ef;"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:640px;background:#ffffff;border:1px solid {RULE};">
<tr><td style="padding:28px 32px 0;" align="center">
  <div style="border-top:3px double {INK};border-bottom:1px solid {INK};padding:14px 0 12px;">
    <div style="font-family:{SERIF};font-size:38px;line-height:1.1;font-weight:bold;color:{INK};letter-spacing:-0.5px;">The <span style="color:{RED};">Vermilion</span> Times</div>
    <div style="font-family:{SANS};font-size:11px;letter-spacing:2.5px;text-transform:uppercase;color:{RED};margin-top:8px;font-weight:bold;">Starbase Louisiana&rsquo;s Local News</div>
  </div>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
    <td style="font-family:{SANS};font-size:11px;letter-spacing:1px;text-transform:uppercase;color:{MUTED};padding:8px 0;border-bottom:1px solid {RULE};" align="left">Vermilion Parish, Louisiana</td>
    <td style="font-family:{SANS};font-size:11px;letter-spacing:1px;text-transform:uppercase;color:{MUTED};padding:8px 0;border-bottom:1px solid {RULE};" align="right">{e(r.get('date',''))}</td>
  </tr></table>
  <p style="margin:18px 0 0;font-family:{SANS};font-size:12px;font-weight:bold;letter-spacing:3px;text-transform:uppercase;color:{INK};">Media Request</p>
</td></tr>
<tr><td style="padding:18px 32px 8px;">{body}</td></tr>
<tr><td style="padding:0 32px 28px;">
  <table role="presentation" cellpadding="0" cellspacing="0" style="border-top:1px solid {INK};padding-top:16px;width:100%;"><tr>
    <td width="64" valign="top" style="padding:16px 14px 0 0;"><img src="{SITE}/img/brand/round-720.png" width="56" height="56" alt="The Vermilion Times" style="display:block;border-radius:50%;"></td>
    <td valign="top" style="padding-top:16px;">
      <div style="font-family:{SERIF};font-size:17px;font-weight:bold;color:{INK};">Brison McPhail</div>
      <div style="font-family:{SANS};font-size:12px;letter-spacing:1px;text-transform:uppercase;color:{MUTED};margin-top:2px;">Publisher, The Vermilion Times</div>
      <div style="font-family:{SANS};font-size:13px;margin-top:8px;"><a href="mailto:news@thevermiliontimes.com" style="color:{RED};text-decoration:none;">news@thevermiliontimes.com</a> &nbsp;&middot;&nbsp; <a href="{SITE}" style="color:{RED};text-decoration:none;">thevermiliontimes.com</a></div>
    </td>
  </tr></table>
</td></tr>
<tr><td style="background:{INK};padding:12px 32px;" align="center">
  <div style="font-family:{SANS};font-size:11px;letter-spacing:1px;color:#cfcfcf;">Please reply to news@thevermiliontimes.com &nbsp;&middot;&nbsp; Independent local news for Vermilion Parish</div>
</td></tr>
</table></td></tr></table></body></html>'''

def text(r):
    out = [r['greeting'], '', r['intro'], '', 'ABOUT THE STORY']
    out += (r['about'] if isinstance(r['about'], list) else [r['about']])
    out += ['', 'WHAT WE ARE ASKING', r['ask']]
    if r.get('questions'):
        out += ['If helpful, these are the questions our readers are asking:'] + [f'{i}. {q}' for i, q in enumerate(r['questions'], 1)]
    for k in ('format', 'timing', 'attribution'):
        if r.get(k): out += ['', k.upper(), r[k]]
    out += ['', r.get('closing', 'Thank you for your time.'), '', 'Brison McPhail', 'Publisher, The Vermilion Times',
            'news@thevermiliontimes.com', SITE]
    return '\n'.join(out)

if __name__ == '__main__':
    r = json.load(open(sys.argv[1])); p = sys.argv[2]
    open(p + '.html', 'w').write(build(r)); open(p + '.txt', 'w').write(text(r))
    print(p + '.html', p + '.txt')
