#!/usr/bin/env python3
"""Vermilion Parish election results, straight from the Secretary of State's live feed.

    python3 tools/results.py 20261103            # print results as Markdown
    python3 tools/results.py 20261103 --json     # raw merged data

Reads the same data the state's results site uses (voterportal.sos.la.gov):
RacesCandidates/ByParish_57.htm (races and candidates) and VotesParish/Votes_57.htm
(vote counts). 57 is Vermilion Parish's ID in that system (58 is Vernon). Results are unofficial
until the state certifies them.
"""
import json, sys, urllib.request

BASE = 'https://voterportal.sos.la.gov/ElectionResults/ElectionResults/Data?blob='
PARISH = 57

def get(blob):
    req = urllib.request.Request(BASE + blob, headers={'User-Agent': 'Mozilla/5.0 (VermilionTimes results)'})
    return json.load(urllib.request.urlopen(req, timeout=30))

def races(date):
    local = get(f'{date}/RacesCandidates/ByParish_{PARISH}.htm')['Races'].get('Race', [])
    multi = get(f'{date}/RacesCandidates_Multiparish.htm')['Races'].get('Race', [])
    votes = get(f'{date}/VotesParish/Votes_{PARISH}.htm')['Races']
    vmap = {r['ID']: r for r in votes.get('Race', [])}
    try:
        allv = get(f'{date}/Votes_Multiparish.htm')
        allv = allv.get('Races', allv)
        wide = {r['ID']: r for r in allv.get('Race', [])}
    except Exception:
        wide = {}
    out, seen = [], set()
    # Vermilion's vote file lists every race on its ballots, local and multiparish;
    # take each race's names from whichever list describes it.
    for r in local + multi:
        if r['ID'] in seen or r['ID'] not in vmap: continue
        seen.add(r['ID'])
        v = vmap.get(r['ID'], {})
        tally = {c['ID']: int(c.get('VoteTotal') or 0) for c in v.get('Choice', [])}
        choices = sorted(({'name': c['Desc'], 'votes': tally.get(c['ID'], 0)} for c in r.get('Choice', [])),
                         key=lambda c: -c['votes'])
        total = sum(c['votes'] for c in choices)
        w = wide.get(r['ID']) if r.get('IsMultiParish') == '1' else None
        wt = {c['ID']: int(c.get('VoteTotal') or 0) for c in (w or {}).get('Choice', [])}
        names = {c['ID']: c['Desc'] for c in r.get('Choice', [])}
        widec = sorted(({'name': names.get(i, i), 'votes': n} for i, n in wt.items()), key=lambda c: -c['votes']) if w else []
        out.append({'wide': widec, 'wide_reporting': int((w or {}).get('PrecinctsReporting') or 0),
                    'wide_expected': int((w or {}).get('PrecinctsExpected') or 0),'title': r['SpecificTitle'], 'level': int(r.get('OfficeLevel') or 0),
                    'elect': int(r.get('NumberToBeElected') or 1), 'runoff': r.get('CanHaveRunoff') == '1',
                    'early_in': int(v.get('NumAbsenteeReporting') or 0) >= int(v.get('NumAbsenteeExpected') or 1),
                    'reporting': int(v.get('PrecinctsReporting') or 0), 'expected': int(v.get('PrecinctsExpected') or 0),
                    'qualified': int(v.get('VoterCountQualified') or 0), 'voted': int(v.get('VoterCountVoted') or 0),
                    'total': total, 'choices': choices})
    return votes.get('VersionDateTime'), out

def markdown(date):
    stamp, rs = races(date)
    lines = []
    for r in sorted(rs, key=lambda r: (r['level'], r['title'])):
        done = r['expected'] and r['reporting'] >= r['expected']
        lines.append(f"### {r['title']}")
        lines.append(f"*{r['reporting']} of {r['expected']} precincts reporting{' (all in)' if done else ''}"
                     f"{'; early and absentee votes counted' if r['early_in'] else ''}*\n")
        for c in r['choices']:
            pct = f"{100 * c['votes'] / r['total']:.1f}%" if r['total'] else '0%'
            lines.append(f"- {c['name']}: **{c['votes']:,}** ({pct})")
        if r['wide']:
            wtot = sum(c['votes'] for c in r['wide'])
            lead = r['wide'][0]
            if wtot:
                lines.append(f"- *All parishes in this race ({r['wide_reporting']} of {r['wide_expected']} precincts): "
                             + '; '.join(f"{c['name']} {c['votes']:,} ({100 * c['votes'] / wtot:.1f}%)" for c in r['wide'][:4]) + '*')
        if done and r['total'] and r['elect'] == 1 and len(r['choices']) > 2 and r['runoff'] \
                and r['choices'][0]['votes'] * 2 <= r['total']:
            lines.append("- *No candidate has a majority; the top two are headed to a runoff.*")
        lines.append('')
    turnout = max(rs, key=lambda r: r['qualified'], default=None)
    head = ''
    if turnout and turnout['qualified'] and turnout['voted']:
        head = (f"Turnout so far: **{turnout['voted']:,}** of {turnout['qualified']:,} registered voters "
                f"({100 * turnout['voted'] / turnout['qualified']:.1f}%) in parishwide races.\n\n")
    return stamp, head + '\n'.join(lines)

if __name__ == '__main__':
    date = sys.argv[1] if len(sys.argv) > 1 else '20261103'
    if '--json' in sys.argv:
        print(json.dumps(races(date), indent=1))
    else:
        stamp, md = markdown(date)
        print(f'<!-- state data version {stamp} -->')
        print(md)
