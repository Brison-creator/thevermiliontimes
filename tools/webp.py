#!/usr/bin/env python3
"""Make phone- and desktop-sized WebP copies of every photo in img/photos/.
build.py serves them automatically (srcset) when they exist. Needs Pillow:
    python3 tools/webp.py
"""
import glob, os
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for f in sorted(glob.glob(os.path.join(ROOT, 'img', 'photos', '*.jpg'))):
    base = f[:-4]
    im = Image.open(f).convert('RGB')
    for w in (640, 1280):
        out = f'{base}-{w}.webp'
        if os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(f): continue
        cp = im.copy()
        if cp.width > w: cp = cp.resize((w, round(cp.height * w / cp.width)), Image.LANCZOS)
        cp.save(out, 'WEBP', quality=72, method=6)
        print(os.path.relpath(out, ROOT), os.path.getsize(out) // 1024, 'KB')
