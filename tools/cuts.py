#!/usr/bin/env python3
"""Draws the engraved section illustrations in img/cuts/ (run once; output is committed).
Every story without a photo shows the illustration for its section."""
import math, os, random
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'img', 'cuts')
I, P = '#14100b', '#faf7ee'
W, H = 640, 400

def sky(horizon, sun=None, rays=True, night=False, step=5):
    o = []
    for y in range(6, horizon, step):
        w = (1.25 if night else 0.5) + 0.9 * (1 - y / horizon)
        if sun and abs(y - sun[1]) < sun[2]:
            dx = math.sqrt(sun[2] ** 2 - (y - sun[1]) ** 2)
            o.append(f'<path d="M0 {y}H{sun[0]-dx-6:.1f}M{sun[0]+dx+6:.1f} {y}H{W}" stroke-width="{w:.2f}"/>')
        else:
            o.append(f'<path d="M0 {y}H{W}" stroke-width="{w:.2f}"/>')
    s = f'<g stroke="{I}" fill="none">{"".join(o)}</g>'
    if sun:
        s += f'<clipPath id="sk"><rect width="{W}" height="{horizon}"/></clipPath>'
    if sun and rays:
        r = []
        for k in range(-6, 7):
            a = math.radians(-90 + k * 13); a1, a2 = a - .05, a + .05
            r.append(f'M{sun[0]} {sun[1]}L{sun[0]+700*math.cos(a1):.1f} {sun[1]+700*math.sin(a1):.1f}L{sun[0]+700*math.cos(a2):.1f} {sun[1]+700*math.sin(a2):.1f}Z')
        s += f'<path d="{"".join(r)}" fill="{P}" clip-path="url(#sk)"/>'
    if sun:
        s += f'<circle cx="{sun[0]}" cy="{sun[1]}" r="{sun[2]}" fill="{P}" stroke="{I}" stroke-width="1.6" clip-path="url(#sk)"/>'
    if night:
        random.seed(5)
        s += ''.join(f'<circle cx="{random.uniform(10,630):.0f}" cy="{random.uniform(10,horizon-40):.0f}" r="{random.uniform(1.2,2.4):.1f}" fill="{P}"/>' for _ in range(40))
    return s

def water(top, step=6):
    random.seed(2); o = []
    for y in range(top, H, step):
        d = f'M0 {y}' + ''.join(f' Q{x+8} {y+random.uniform(-1.6,1.6):.1f} {x+16} {y}' for x in range(0, W, 16))
        o.append(f'<path d="{d}" stroke-width="{0.7+(y-top)/150:.2f}"/>')
    return f'<g stroke="{I}" fill="none">{"".join(o)}</g>'

def ground(top, rows=True):
    s = f'<rect y="{top}" width="{W}" height="{H-top}" fill="{I}"/>'
    if rows:
        s += f'<g stroke="{P}" stroke-width="1" opacity=".55">' + ''.join(
            f'<path d="M{W/2} {top} L{x} {H}"/>' for x in range(-400, W + 400, 40)) + '</g>'
    return s

def treeline(y, seed=1):
    random.seed(seed); pts = [(0, y)]; x = 0
    while x < W:
        x += random.uniform(8, 18); pts.append((x, y - random.uniform(6, 20))); x += random.uniform(3, 7); pts.append((x, y - random.uniform(2, 7)))
    return f'<path d="M{" L".join(f"{a:.0f} {b:.0f}" for a,b in pts)} L{W} {y} L{W} {y+14} L0 {y+14}Z" fill="{I}"/>'

def oak(cx, base, scale=1.0, seed=3):
    random.seed(seed); s = []
    s.append(f'<path d="M{cx-6*scale} {base} C{cx-4*scale} {base-30*scale} {cx-8*scale} {base-50*scale} {cx-14*scale} {base-62*scale} L{cx+12*scale} {base-62*scale} C{cx+6*scale} {base-48*scale} {cx+6*scale} {base-28*scale} {cx+8*scale} {base}Z" fill="{I}"/>')
    for _ in range(int(90*scale)):
        x = random.gauss(cx, 46*scale); y = random.gauss(base-78*scale, 16*scale)
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{random.uniform(5,10)*scale:.1f}" fill="{I}"/>')
    return ''.join(s)

def frame(body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img"><title>{title}</title>'
            f'<rect width="{W}" height="{H}" fill="{P}"/>{body}'
            f'<rect x="1" y="1" width="{W-2}" height="{H-2}" fill="none" stroke="{I}" stroke-width="2"/></svg>')

def courthouse():
    b = sky(300, sun=(520, 120, 34), rays=True)
    b += f'<rect y="300" width="{W}" height="100" fill="{I}"/>'
    # steps, base, columns, pediment, dome, flag
    b += f'<g fill="{I}"><rect x="150" y="286" width="340" height="14"/><rect x="164" y="272" width="312" height="14"/><rect x="178" y="170" width="284" height="102" fill="{P}" stroke="{I}" stroke-width="3"/>'
    b += ''.join(f'<rect x="{x}" y="176" width="16" height="96"/>' for x in range(192, 462, 44))
    b += f'<path d="M168 170 L320 116 L472 170Z"/><path d="M196 164 L320 124 L444 164Z" fill="{P}"/><circle cx="320" cy="148" r="9" fill="{I}"/>'
    b += f'<rect x="276" y="92" width="88" height="22"/><path d="M282 92 Q320 40 358 92Z"/><rect x="318" y="20" width="3" height="34"/><path d="M321 22 h30 l-6 8 6 8 h-30Z"/></g>'
    b += oak(70, 300, 1.0, 4) + oak(580, 300, 0.9, 6)
    b += f'<g stroke="{P}" stroke-width="1.2">' + ''.join(f'<path d="M{x} 300 L{x-30} 400"/>' for x in range(160, 500, 26)) + '</g>'
    return frame(b, 'Engraving of a columned parish courthouse under a rising sun')

def rocket():
    b = sky(300, sun=(140, 300, 70), rays=True)
    b += treeline(300, 9) + water(312)
    # launch tower lattice
    t = [f'<rect x="372" y="70" width="34" height="232" fill="none" stroke="{I}" stroke-width="3"/>']
    t += [f'<path d="M372 {y} L406 {y+22} M406 {y} L372 {y+22}" stroke="{I}" stroke-width="1.6"/>' for y in range(70, 300, 22)]
    t += [f'<rect x="352" y="96" width="24" height="5" fill="{I}"/><rect x="352" y="170" width="24" height="5" fill="{I}"/>']
    b += ''.join(t)
    # generic two-stage rocket, plain stainless with outline (no markings)
    b += f'<path d="M318 300 L318 120 Q318 64 334 40 Q350 64 350 120 L350 300Z" fill="{P}" stroke="{I}" stroke-width="3"/>'
    b += f'<path d="M318 190 H350 M318 196 H350" stroke="{I}" stroke-width="2"/><path d="M318 136 l-14 26 v12 l14 -8Z M350 136 l14 26 v12 l-14 -8Z" fill="{I}"/>'
    b += f'<path d="M318 282 l-16 18 h16Z M350 282 l16 18 h-16Z" fill="{I}"/>'
    b += f'<g stroke="{I}" stroke-width="1" opacity=".55">' + ''.join(f'<path d="M{x} 124 V296"/>' for x in (326, 334, 342)) + '</g>'
    b += f'<rect x="296" y="300" width="128" height="10" fill="{I}"/>'
    return frame(b, 'Engraving of a rocket on its launch tower over the coastal marsh at sunrise')

def badge():
    b = sky(400, step=6)
    cx, cy = 320, 205; pts = []
    for k in range(10):
        r = 150 if k % 2 == 0 else 66; a = math.radians(-90 + k * 36)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    star = 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in pts) + 'Z'
    b += f'<path d="{star}" fill="{P}" stroke="{I}" stroke-width="4" stroke-linejoin="round"/>'
    b += ''.join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="11" fill="{I}"/>' for x, y in pts[::2])
    inner = 'M' + ' L'.join(f'{cx+(x-cx)*.78:.1f} {cy+(y-cy)*.78:.1f}' for x, y in pts) + 'Z'
    b += f'<path d="{inner}" fill="none" stroke="{I}" stroke-width="1.5"/>'
    b += f'<circle cx="{cx}" cy="{cy}" r="52" fill="{I}"/><circle cx="{cx}" cy="{cy}" r="44" fill="{P}"/><circle cx="{cx}" cy="{cy}" r="38" fill="none" stroke="{I}" stroke-width="1.4"/>'
    b += f'<path d="M{cx} {cy-26} l7 16 17 1 -13 11 4 17 -15 -9 -15 9 4 -17 -13 -11 17 -1Z" fill="{I}"/>'
    return frame(b, 'Engraving of a sheriff\'s star badge')

def schoolhouse():
    b = sky(310, sun=(110, 110, 30)) + ground(310, rows=False)
    b += f'<g fill="{I}"><path d="M200 310 V200 L320 140 L440 200 V310Z"/><rect x="300" y="78" width="40" height="70"/><path d="M294 80 L320 52 L346 80Z"/><rect x="318" y="20" width="3" height="34"/><path d="M321 22 h28 l-6 7 6 7 h-28Z"/></g>'
    b += f'<g fill="{P}"><path d="M308 96 h24 v30 h-24Z"/><rect x="292" y="250" width="56" height="60"/>' + ''.join(f'<rect x="{x}" y="226" width="34" height="44"/>' for x in (222, 384)) + '</g>'
    b += f'<g stroke="{I}" stroke-width="3"><path d="M239 226 V270 M222 248 H256 M401 226 V270 M384 248 H418 M320 250 V310"/></g><path d="M320 100 a8 8 0 0 1 8 8 v8 h-16 v-8 a8 8 0 0 1 8 -8Z" fill="{I}"/>'
    b += oak(560, 310, 1.0, 8) + oak(80, 310, 0.8, 2)
    return frame(b, 'Engraving of a country schoolhouse with a bell tower')

def stadium():
    b = sky(300, night=True) + ground(300, rows=False)
    b += f'<g stroke="{P}" stroke-width="2">' + ''.join(f'<path d="M{320-(400-y)*0.2*(k):.0f} {y}"/>' for k in range(1) for y in ()) + '</g>'
    b += f'<g stroke="{P}" stroke-width="1.6">' + ''.join(f'<path d="M{320+(x-320)*0.35:.1f} 300 L{x} 400"/>' for x in range(-200, 860, 80)) + ''.join(f'<path d="M0 {y} H640"/>' for y in (318, 342, 370)) + '</g>'
    # goalpost
    b += f'<g stroke="{P}" stroke-width="7" fill="none" stroke-linecap="round"><path d="M320 300 V220 M262 220 H378 M262 220 V120 M378 220 V120"/></g>'
    # light towers with glowing banks
    for x in (70, 570):
        b += f'<path d="M{x} 300 L{x+4} 90 L{x+8} 300Z" fill="{P}"/>'
        b += f'<rect x="{x-24}" y="66" width="56" height="30" fill="{P}"/>' + ''.join(f'<circle cx="{x-14+i*12}" cy="{74+j*13}" r="4" fill="{I}"/>' for i in range(4) for j in range(2))
        b += f'<path d="M{x+4} 96 L{320 if x<320 else 320} 300 L{x+90 if x<320 else x-90} 300Z" fill="{P}" opacity=".12"/>'
    return frame(b, 'Engraving of a high school football field under Friday night lights')

def mainstreet():
    b = sky(150, sun=(560, 110, 28)) + f'<rect y="300" width="{W}" height="100" fill="{I}"/>'
    xs = [(20, 130, 150), (150, 140, 120), (290, 120, 160), (410, 110, 130), (520, 100, 150)]
    for x, w, h in xs:
        top = 300 - h
        b += f'<rect x="{x}" y="{top}" width="{w}" height="{h}" fill="{P}" stroke="{I}" stroke-width="3"/>'
        b += f'<rect x="{x-4}" y="{top-10}" width="{w+8}" height="12" fill="{I}"/>'
        b += ''.join(f'<rect x="{x+12+i*((w-24)//3)}" y="{top+16}" width="{(w-24)//3-10}" height="30" fill="{I}"/>' for i in range(3) if h > 120)
        aw = top + h - 92
        b += f'<path d="M{x+6} {aw} H{x+w-6} L{x+w+2} {aw+22} H{x-2}Z" fill="{I}"/>' + ''.join(f'<path d="M{x+6+i*14} {aw} L{x+2+i*14} {aw+22}" stroke="{P}" stroke-width="5"/>' for i in range(0, (w-8)//14, 2))
        b += f'<rect x="{x+w//2-14}" y="{300-56}" width="28" height="56" fill="{I}"/><rect x="{x+10}" y="{300-52}" width="{w//2-34}" height="34" fill="{I}" opacity=".85"/>'
    b += f'<g stroke="{P}" stroke-width="2">' + ''.join(f'<path d="M{x} 352 h28"/>' for x in range(10, 640, 60)) + '</g>'
    return frame(b, 'Engraving of storefronts with awnings along a small-town main street')

def shrimpboat():
    b = sky(250, sun=(500, 250, 50)) + treeline(250, 4) + water(262)
    hull = 'M140 300 C200 318 380 318 450 296 L470 278 L150 282Z'
    b += f'<path d="{hull}" fill="{I}"/><rect x="330" y="236" width="70" height="44" fill="{I}"/><rect x="342" y="246" width="16" height="14" fill="{P}"/><rect x="368" y="246" width="16" height="14" fill="{P}"/>'
    b += f'<g stroke="{I}" stroke-width="4" stroke-linecap="round" fill="none"><path d="M300 282 V120"/><path d="M300 140 L150 230 M300 140 L460 190 M300 120 L220 282 M300 120 L380 282"/></g>'
    b += f'<g stroke="{I}" stroke-width="1.2" fill="none">' + ''.join(f'<path d="M150 230 Q{120+i*6} {250+i*8} {110+i*4} {290+i*6}"/>' for i in range(6)) + ''.join(f'<path d="M460 190 Q{490+i*6} {220+i*8} {500+i*4} {270+i*6}"/>' for i in range(6)) + '</g>'
    b += f'<path d="M150 322 h300 M180 330 h240 M220 338 h160" stroke="{I}" stroke-width="1.6"/>'
    return frame(b, 'Engraving of a shrimp boat with its nets out at sunset')

def church():
    b = sky(310, sun=(520, 140, 32)) + ground(310, rows=False)
    b += f'<g fill="{I}"><path d="M210 310 V200 L300 150 L390 200 V310Z"/><rect x="270" y="110" width="60" height="200"/><path d="M262 112 L300 30 L338 112Z"/><rect x="298" y="6" width="4" height="30"/><rect x="290" y="14" width="20" height="4"/></g>'
    b += f'<g fill="{P}"><path d="M286 310 V262 a14 14 0 0 1 28 0 V310Z"/><path d="M290 150 a10 10 0 0 1 20 0 v26 h-20Z"/>' + ''.join(f'<path d="M{x} 270 v-34 a9 9 0 0 1 18 0 v34Z"/>' for x in (226, 352)) + '</g>'
    b += oak(90, 310, 1.1, 11) + oak(560, 310, 0.95, 12)
    m = []
    random.seed(13)
    for _ in range(30):
        x = random.choice([random.uniform(40, 140), random.uniform(510, 610)]); y = random.uniform(232, 252); L = random.uniform(16, 40)
        m.append(f'M{x:.0f} {y:.0f}' + ''.join(f' l{random.uniform(-2,2):.1f} 6' for _ in range(int(L // 6))))
    b += f'<path d="{"".join(m)}" stroke="{I}" stroke-width="1.5" fill="none"/>'
    return frame(b, 'Engraving of a country church with a steeple between live oaks')

def quill():
    b = sky(400, step=6)
    b += f'<rect x="120" y="70" width="400" height="280" fill="{P}" stroke="{I}" stroke-width="3"/>'
    b += f'<g stroke="{I}" stroke-width="2">' + ''.join(f'<path d="M150 {y} H{490 - (40 if y % 3 == 0 else 0)}"/>' for y in range(110, 330, 22)) + '</g>'
    b += f'<path d="M420 300 h80 l-8 -50 h-64Z" fill="{I}"/><ellipse cx="460" cy="250" rx="34" ry="8" fill="{I}"/>'
    b += f'<path d="M458 252 C470 180 520 90 600 40 C560 110 520 170 466 254Z" fill="{P}" stroke="{I}" stroke-width="3"/>'
    b += f'<g stroke="{I}" stroke-width="1.2">' + ''.join(f'<path d="M{470+i*9} {226-i*13} L{490+i*11} {214-i*14}"/>' for i in range(12)) + '</g>'
    return frame(b, 'Engraving of a quill pen in an inkwell on a written page')

def candle():
    b = sky(400, step=6, night=True)
    b += f'<rect x="282" y="190" width="76" height="170" fill="{P}" stroke="{I}" stroke-width="3"/><path d="M282 196 q10 14 0 30" stroke="{I}" stroke-width="3" fill="none"/>'
    b += f'<rect x="232" y="356" width="176" height="18" fill="{P}"/><path d="M320 120 C300 150 304 176 320 186 C336 176 340 150 320 120Z" fill="{P}"/><path d="M320 150 C312 164 314 176 320 180 C326 176 328 164 320 150Z" fill="{I}"/><rect x="318" y="180" width="4" height="12" fill="{P}"/>'
    b += ''.join(f'<path d="M320 152 L{320+120*math.cos(math.radians(a)):.0f} {152+120*math.sin(math.radians(a)):.0f}" stroke="{P}" stroke-width="2" opacity=".5"/>' for a in range(-160, -10, 15))
    # lilies
    for x, y, f in ((170, 300, 1), (470, 300, -1)):
        b += f'<path d="M{x} 374 C{x} 340 {x+10*f} 320 {x+4*f} {y}" stroke="{P}" stroke-width="4" fill="none"/>'
        b += f'<path d="M{x+4*f} {y} c{-24*f} -10 {-30*f} -40 {-16*f} -52 c4 22 12 36 {16*f} 52Z M{x+4*f} {y} c{24*f} -10 {30*f} -40 {16*f} -52 c-4 22 -12 36 {-16*f} 52Z M{x+4*f} {y} c-6 -24 -2 -48 0 -60 c2 12 6 36 0 60Z" fill="{P}"/>'
    return frame(b, 'Engraving of a lit memorial candle between two lilies')

def ballot():
    b = sky(400, step=6)
    b += f'<path d="M200 200 L440 200 L460 360 L180 360Z" fill="{P}" stroke="{I}" stroke-width="4"/><path d="M200 200 L230 160 H410 L440 200Z" fill="{I}"/><rect x="270" y="172" width="100" height="10" fill="{P}"/>'
    b += f'<rect x="282" y="62" width="76" height="120" fill="{P}" stroke="{I}" stroke-width="3" transform="rotate(-6 320 120)"/>'
    b += f'<g transform="rotate(-6 320 120)" stroke="{I}" stroke-width="2"><rect x="294" y="80" width="12" height="12" fill="none"/><path d="M296 86 l4 5 8 -12" stroke-width="3" fill="none"/><path d="M312 86 h36 M294 108 h54 M294 122 h54 M294 136 h40"/></g>'
    b += f'<g stroke="{I}" stroke-width="2.2">' + ''.join(f'<path d="M{200+i*24} 216 L{186+i*26.5} 344"/>' for i in range(11)) + '</g>'
    b += f'<rect x="266" y="250" width="108" height="50" fill="{P}" stroke="{I}" stroke-width="3"/><text x="320" y="284" font-family="Georgia,serif" font-size="26" font-weight="bold" text-anchor="middle" fill="{I}">VOTE</text>'
    return frame(b, 'Engraving of a ballot dropping into a ballot box')

CUTS = {'government': courthouse, 'starbase': rocket, 'safety': badge, 'schools': schoolhouse, 'sports': stadium,
        'business': mainstreet, 'land-water': shrimpboat, 'faith': church, 'opinion': quill, 'obituaries': candle, 'elections': ballot}
if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for name, fn in CUTS.items():
        open(os.path.join(OUT, name + '.svg'), 'w').write(fn())
    print('drew', ', '.join(CUTS))
