#!/usr/bin/env python3
"""Extract every outbound affiliate link from site/, check well-formedness + labels, and curl each unique Seeed URL.
Also: tag/affiliate param appears exactly once per URL, every accessory in accessories.py is linked, new pages are in
nav + sitemap. `--amazon` re-fetches every accessory ASIN and checks the product title still matches."""
import os, re, sys, json, html, subprocess, collections, urllib.parse, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from accessories import ACC
ROOT = os.path.join(HERE, '..', 'site')
TAG, SEEED_Q = 'edgetokens-20', {'sensecap_affiliate': ['WwUWAV9'], 'referring_service': ['link']}
A_RE = re.compile(r'<a\s([^>]*?)>(.*?)</a>', re.S)
def attrs(s): return {k: html.unescape(v) for k, v in re.findall(r'([\w-]+)="([^"]*)"', s)}
links, errs = [], []          # (file, url, label, kind, attrs)
for dp, _, fs in os.walk(ROOT):
    for f in fs:
        if not f.endswith('.html'): continue
        path = os.path.join(dp, f); rel = os.path.relpath(path, ROOT); s = open(path, encoding='utf-8').read()
        for m in A_RE.finditer(s):
            a = attrs(m.group(1)); u = a.get('href', '')
            host = urllib.parse.urlsplit(u).netloc
            # Shop affiliate links only. wiki.seeedstudio.com is a benchmark source, not a buy link.
            if host in ('www.amazon.com', 'www.seeedstudio.com'):
                links.append((rel, u, html.unescape(re.sub('<[^>]+>', '', m.group(2))).strip(), 'html', a))
        pj = re.search(r'<script type="application/json" id="pick-data">(.*?)</script>', s, re.S)
        if pj:
            for r in json.loads(pj.group(1).replace('<\\/', '</')):
                for b in r['buy']: links.append((rel, b['u'], b['l'], 'pick-json', {'rel': 'sponsored nofollow noopener', 'target': '_blank'}))
def check(rel, u, label, kind, a):
    e = []
    if any(c in u for c in ' "<>') or '&amp;' in u or re.search(r'%(?![0-9A-Fa-f]{2})', u): e.append('bad encoding')
    p = urllib.parse.urlsplit(u); q = urllib.parse.parse_qs(p.query, keep_blank_values=True)
    if p.scheme != 'https': e.append('not https')
    if a.get('rel') != 'sponsored nofollow noopener': e.append(f'rel={a.get("rel")!r}')
    if a.get('target') != '_blank': e.append(f'target={a.get("target")!r}')
    if p.netloc == 'www.amazon.com':
        if q.get('tag') != [TAG]: e.append(f'tag={q.get("tag")}')
        if p.path.startswith('/dp/'):
            if not re.fullmatch(r'/dp/[A-Z0-9]{10}', p.path): e.append('bad ASIN path')
            if set(q) != {'tag'}: e.append(f'extra params {sorted(q)}')
            if not (label == 'Buy on Amazon' or label.startswith('Amazon: ')): e.append(f'label {label!r} on product page')
        elif p.path == '/s':
            if set(q) != {'k', 'tag'} or len(q['k']) != 1 or not q['k'][0].strip(): e.append('bad search params')
            if not (label == 'Check price on Amazon' or label.startswith('Amazon: ')): e.append(f'label {label!r} on search link')
        else: e.append('unexpected amazon path')
    elif p.netloc == 'www.seeedstudio.com':
        if q != SEEED_Q: e.append(f'seeed params {q}')
        if not p.path.endswith('.html'): e.append('seeed path')
        if not (label == 'Buy at Seeed Studio' or label.startswith('Seeed: ')): e.append(f'label {label!r}')
    else: e.append(f'unexpected domain {p.netloc}')
    if u.count('?') != 1: e.append('"?" count != 1')
    if p.netloc == 'www.amazon.com' and (u.count('tag=') != 1 or u.count(TAG) != 1): e.append('tag not exactly once')
    if p.netloc == 'www.seeedstudio.com' and (u.count('sensecap_affiliate=') != 1 or u.count('referring_service=') != 1): e.append('seeed affiliate params not exactly once')
    return e
bad = 0
for l in links:
    e = check(*l)
    if e: bad += 1; print('BAD', l[0], l[1], l[2], e)
# duplicates: same URL twice inside one buy group (same file, adjacent) is a bug
dups = 0
for f in set(l[0] for l in links):
    s = open(os.path.join(ROOT, f), encoding='utf-8').read()
    for blk in re.findall(r'<span class="buy">(.*?)</span>|<div class="ctas">(.*?)</div>', s, re.S):
        us = re.findall(r'href="([^"]+)"', ''.join(blk)); us = [x for x in us if 'amazon.' in x or 'seeedstudio.' in x]
        if len(us) != len(set(us)): dups += 1; print('DUP in button group', f, us)
    pj = re.search(r'id="pick-data">(.*?)</script>', s, re.S)
    if pj:
        for r in json.loads(pj.group(1).replace('<\\/', '</')):
            us = [b['u'] for b in r['buy']]
            if len(us) != len(set(us)): dups += 1; print('DUP in pick entry', f, r['b'], us)
uniq = collections.Counter(l[1] for l in links)
print(f'\n{len(links)} affiliate links, {len(uniq)} unique, {bad} malformed, {dups} duplicate-in-group')
for u, n in sorted(uniq.items()): print(f'{n:4d}  {u}')
# accessories: every catalog item must be linked somewhere, exactly as built
acc_bad = 0
site_urls = set(uniq)
for k, a in ACC.items():
    exp = (f'https://www.amazon.com/dp/{a["asin"]}?tag={TAG}' if a.get('asin') else
           f'https://www.amazon.com/s?k={urllib.parse.quote_plus(a["search"])}&tag={TAG}')
    n = uniq.get(exp, 0)
    sn = 0
    if a.get('seeed'):
        su = a['seeed'] + '?sensecap_affiliate=WwUWAV9&referring_service=link'; sn = uniq.get(su, 0)
        if not sn: acc_bad += 1; print('ACC MISSING seeed', k, su)
    if not n: acc_bad += 1; print('ACC MISSING amazon', k, exp)
    print(f'  acc {k:15s} amazon x{n:<3d} seeed x{sn:<3d} {"dp/"+a["asin"] if a.get("asin") else "search: "+a["search"]}')
# new pages in nav + sitemap
sm = open(os.path.join(ROOT, 'sitemap.xml')).read(); idx = open(os.path.join(ROOT, 'index.html')).read()
for need in ('kits/', 'guides/best-board-for-local-llm/', 'guides/raspberry-pi-5-local-llm-setup/', 'guides/jetson-orin-nano-super-local-llm/'):
    if f'https://edgetokens.dev/{need}<' not in sm: acc_bad += 1; print('NOT IN SITEMAP', need)
    if not os.path.exists(os.path.join(ROOT, need, 'index.html')): acc_bad += 1; print('PAGE MISSING', need)
if 'href="kits/index.html"' not in idx.split('</nav>')[0]: acc_bad += 1; print('kits/ not in main nav')
for f in [l[0] for l in links]:
    pass
footer_ok = all('Every number links to its public source' in open(os.path.join(dp, f)).read() and 'As an Amazon Associate' in open(os.path.join(dp, f)).read()
                for dp, _, fs in os.walk(ROOT) for f in fs if f.endswith('.html'))
if not footer_ok: acc_bad += 1; print('FOOTER DISCLOSURE missing on some page')
print(f'accessory/page checks: {acc_bad} problems; footer disclosures on every page: {footer_ok}')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'
fail = 0
print('\nSeeed status:')
for u in sorted(x for x in uniq if 'seeedstudio.' in x):
    r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code} %{num_redirects}', '-A', UA, '--max-time', '30', u], capture_output=True, text=True).stdout
    code = r.split()[0] if r else '000'
    if code != '200': fail += 1
    print(' ', r, u)
amz_fail = 0
if '--amazon' in sys.argv:
    print('\nAmazon accessory titles (live fetch):')
    for k, a in ACC.items():
        if not a.get('asin'): continue
        t = None
        for i in range(3):
            r = subprocess.run(['curl', '-s', '-L', '--compressed', '-A', UA, '-H', 'Accept-Language: en-US,en;q=0.9', '--max-time', '30', f'https://www.amazon.com/dp/{a["asin"]}'], capture_output=True, text=True, errors='ignore').stdout
            m = re.search(r'id="productTitle"[^>]*>(.*?)<', r, re.S)
            if m: t = html.unescape(m.group(1)).strip(); break
            time.sleep(3)
        ok = bool(t) and all(w.lower() in t.lower() for w in a['verify'])
        if not ok: amz_fail += 1
        print(f'  {"OK " if ok else "BAD"} {a["asin"]} {k}: {t}')
sys.exit(1 if bad or dups or fail or acc_bad or amz_fail else 0)
