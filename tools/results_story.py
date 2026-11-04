#!/usr/bin/env python3
"""Rebuild the election-night results story: hand-written top + live results from tools/results.py.

    python3 tools/results_story.py articles/2026-11-03-vermilion-parish-election-results.md 20261103

Everything above the line `<!-- RESULTS -->` is kept; everything below is replaced
with the latest numbers from the Secretary of State's feed.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import results

path, date = sys.argv[1], sys.argv[2]
text = open(path, encoding='utf-8').read()
top = text.split('<!-- RESULTS -->')[0].rstrip()
stamp, md = results.markdown(date)
open(path, 'w', encoding='utf-8').write(f"{top}\n\n<!-- RESULTS -->\n## Every race on Vermilion Parish ballots\n\n"
    f"*Unofficial results from the Louisiana Secretary of State, {'final count' if stamp.startswith('1900') else 'data as of ' + stamp[11:16] + ' Central'}.*\n\n{md}\n")
print('updated', path, 'state data', stamp)
