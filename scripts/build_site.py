import urllib.parse
"""Static site generator for EdgeTokens. Output: site/ (plain HTML/CSS/JS, no build deps)."""
import csv, json, os, html, shutil, collections, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from accessories import ACC, INCLUDED, SRC_DATE
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'site')
SITE = 'EdgeTokens'
BASE_URL = 'https://edgetokens.dev'
B = list(csv.DictReader(open(os.path.join(ROOT,'data','benchmarks.csv'))))
BD = list(csv.DictReader(open(os.path.join(ROOT,'data','boards.csv'))))
for r in B: r['gen_tps'] = float(r['gen_tps'])

P = {  # platform display names + short blurbs (descriptive, no numbers)
 'rpi5': ('Raspberry Pi 5', 'Raspberry Pi 5 (CPU)', 'The default maker board. LLMs run on the four Cortex-A76 CPU cores with llama.cpp or Ollama.'),
 'rpi5-ai-hat-plus-2': ('Raspberry Pi 5 + AI HAT+ 2', 'Pi 5 + AI HAT+ 2 (Hailo-10H)', 'A Hailo-10H NPU with its own 8GB RAM on a HAT, running Hailo-compiled models through hailo-ollama.'),
 'rpi5-cluster': ('Raspberry Pi 5 cluster', 'Pi 5 cluster (distributed-llama)', 'Several Pi 5 boards splitting one model over Ethernet with distributed-llama.'),
 'jetson-orin-nano-super': ('Jetson Orin Nano Super', 'Jetson Orin Nano Super', 'NVIDIA\'s small CUDA board in its JetPack 6.2 "Super" (25W / MAXN SUPER) power mode.'),
 'jetson-orin-nano': ('Jetson Orin Nano', 'Jetson Orin Nano (original / mode not stated)', 'Orin Nano results in the original power mode, or where the source did not state the mode.'),
 'jetson-orin-nx-8gb': ('Jetson Orin NX 8GB', 'Jetson Orin NX 8GB (original mode)', 'Orin NX 8GB module in its original power mode.'),
 'jetson-orin-nx-8gb-super': ('Jetson Orin NX 8GB Super', 'Jetson Orin NX 8GB (Super mode)', 'Orin NX 8GB module with JetPack 6.2 Super mode.'),
 'jetson-orin-nx-16gb': ('Jetson Orin NX 16GB', 'Jetson Orin NX 16GB (original mode)', 'Orin NX 16GB module in its original power mode.'),
 'jetson-orin-nx-16gb-super': ('Jetson Orin NX 16GB Super', 'Jetson Orin NX 16GB (Super mode)', 'Orin NX 16GB module with JetPack 6.2 Super mode.'),
 'jetson-agx-orin': ('Jetson AGX Orin', 'Jetson AGX Orin', 'The big Orin dev kit. Not cheap, but a useful ceiling for edge numbers.'),
 'jetson-agx-thor': ('Jetson AGX Thor', 'Jetson AGX Thor', 'NVIDIA\'s Blackwell-based robotics dev kit, the top of the edge range.'),
 'rk3588': ('Rockchip RK3588', 'RK3588 boards (NPU)', 'The 6-TOPS NPU in Orange Pi 5, Radxa ROCK 5, Indiedroid Nova, ODROID-M2 and friends, driven by RKLLM.'),
 'rk3576': ('Rockchip RK3576', 'RK3576 boards (NPU)', 'Rockchip\'s mid-range SoC with an NPU, found on boards like the Radxa ROCK 4D.'),
 'm5stack-module-llm': ('M5Stack Module LLM', 'M5Stack Module LLM (AX630C)', 'A tiny 54mm module with an Axera AX630C NPU, running StackFlow.'),
 'm5stack-ai-pyramid': ('M5Stack AI Pyramid', 'M5Stack AI Pyramid (AX8850)', 'M5Stack\'s AX8850-based AI box.'),
 'm5stack-llm8850': ('M5Stack LLM8850', 'M5Stack LLM8850 M.2 (AX8850)', 'An AX8850 accelerator on an M.2 card, for adding an NPU to another host.'),
 'arduino-uno-q': ('Arduino UNO Q', 'Arduino UNO Q', 'Arduino\'s Linux + microcontroller board. Results so far are CPU-only.'),
}
SHORT = {k:v[0] for k,v in P.items()}
MODEL_NAME = {}
for r in B:
    MODEL_NAME.setdefault(r['model_slug'], re.sub(r'\s*\(.*?\)','',r['model']).replace(' Instruct',''))

def esc(s): return html.escape(str(s), quote=True)
def fmt(v): return ('%.2f' % v).rstrip('0').rstrip('.') if isinstance(v,float) else v
def verdict(best):
    if best >= 10: return ('yes','Yes, at a comfortable chat speed')
    if best >= 4: return ('ok','Yes, usable but slower than reading speed')
    return ('slow','Technically yes, but slowly')

CSS = open(os.path.join(ROOT,'scripts','style.css')).read() if os.path.exists(os.path.join(ROOT,'scripts','style.css')) else ''

NAV = [('index.html','Leaderboard','home'),('value/index.html','Best value','value'),('pick/index.html','Which board?','pick'),('kits/index.html','Starter kits','kits'),('boards/index.html','Boards','boards'),('submit/index.html','Submit a run','submit')]
# Dark is the default even when the OS is light; a saved choice wins. Also flags JS/IO early so nothing shifts after load.
THEME_JS = "(function(){var r=document.documentElement,t='dark';try{t=localStorage.getItem('et-theme')||'dark'}catch(e){}r.dataset.theme=t;r.classList.add('js');if('IntersectionObserver' in window&&!(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches))r.classList.add('io')})()"
MARK_SVG = '<svg viewBox="0 0 32 32" width="22" height="22" aria-hidden="true" focusable="false"><defs><linearGradient id="etg" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#30d158"/><stop offset="1" stop-color="#40cbe0"/></linearGradient></defs><rect width="32" height="32" rx="8" fill="#0b0b0c" stroke="rgba(255,255,255,.14)"/><rect x="7" y="17" width="4" height="8" rx="2" fill="url(#etg)"/><rect x="14" y="12" width="4" height="13" rx="2" fill="url(#etg)"/><rect x="21" y="7" width="4" height="18" rx="2" fill="url(#etg)"/></svg>'
FAVICON = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><defs><linearGradient id="g" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#30d158"/><stop offset="1" stop-color="#40cbe0"/></linearGradient></defs><rect width="32" height="32" rx="8" fill="#000"/><rect x="7" y="17" width="4" height="8" rx="2" fill="url(#g)"/><rect x="14" y="12" width="4" height="13" rx="2" fill="url(#g)"/><rect x="21" y="7" width="4" height="18" rx="2" fill="url(#g)"/></svg>'
SUN = '<svg class="sun" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><circle cx="12" cy="12" r="4.2" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M5.3 18.7l1.6-1.6M17.1 6.9l1.6-1.6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'
MOON = '<svg class="moon" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M20 14.6A8 8 0 0 1 9.4 4a8 8 0 1 0 10.6 10.6z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>'

def page(title, desc, body, path, depth, active=''):
    pre = '../' * depth
    canon = BASE_URL + '/' + ('' if path == 'index.html' else path)
    nav = ''.join(f'<a href="{pre}{u}"{" aria-current=page" if k==active else ""}>{t}</a>' for u,t,k in NAV)
    logo = f'<a class="logo" href="{pre}index.html" aria-label="EdgeTokens home">{MARK_SVG}<span>EdgeTokens</span></a>'
    return f'''<!doctype html><html lang="en" data-theme="dark"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(canon)}">
<meta property="og:type" content="website"><meta property="og:site_name" content="{SITE}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(canon)}"><meta name="twitter:card" content="summary">
<meta name="color-scheme" content="dark light"><meta name="theme-color" content="#000000">
<script>{THEME_JS}</script>
<link rel="stylesheet" href="{pre}assets/style.css">
<link rel="icon" type="image/svg+xml" href="{pre}assets/favicon.svg">
</head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="top" id="top"><div class="wrap topbar">{logo}
<nav class="nav" id="nav" aria-label="Main">{nav}<a class="navcsv" href="{pre}data/benchmarks.csv" download>CSV</a></nav>
<button class="iconbtn theme" type="button" id="theme" aria-label="Toggle light and dark mode" title="Toggle light / dark">{SUN}{MOON}</button>
<button class="iconbtn menu" type="button" id="menu" aria-label="Menu" aria-expanded="false" aria-controls="nav"><span></span><span></span></button></div></header>
<main id="main" class="wrap">{body}</main>
<section class="news reveal" aria-labelledby="nl-h"><div class="wrap narrow"><h2 id="nl-h">Stay in the loop.</h2><p>New boards, new runtimes, new numbers. One email a month, no hype.</p>
<form class="nl" action="https://buttondown.com/api/emails/embed-subscribe/edgetokens" method="post" target="_blank" onsubmit="this.querySelector('.ok').hidden=false;">
<input type="email" name="email" required placeholder="you@workbench.dev" aria-label="Email"><input type="hidden" name="embed" value="1"><button>Subscribe</button><span class="ok" hidden>Almost done! Check your inbox to confirm.</span></form></div></section>
<footer class="foot"><div class="wrap">
<nav class="footnav" aria-label="Footer"><a href="{pre}index.html">Leaderboard</a><a href="{pre}value/index.html">Best value</a><a href="{pre}pick/index.html">Which board?</a><a href="{pre}kits/index.html">Starter kits</a><a href="{pre}guides/best-board-for-local-llm/index.html">Best board for local LLMs</a><a href="{pre}guides/raspberry-pi-5-local-llm-setup/index.html">Pi 5 local LLM setup</a><a href="{pre}guides/jetson-orin-nano-super-local-llm/index.html">Jetson Orin Nano Super guide</a><a href="{pre}boards/index.html">Boards</a><a href="{pre}submit/index.html">Submit a run</a><a href="{pre}about/index.html">Methodology</a><a href="{pre}data/benchmarks.csv" download>Download the dataset (CSV)</a></nav>
<p class="disc">Every number links to its public source. We never estimate speeds. As an Amazon Associate, EdgeTokens earns from qualifying purchases. EdgeTokens may also earn a commission from Seeed Studio purchases made through our links. <a href="{pre}about/index.html">Methodology</a> · <a href="{pre}data/benchmarks.csv" download>Download the dataset (CSV)</a></p>
<p class="colophon">EdgeTokens · Real LLM speeds on small boards. Every number sourced.</p></div></footer>
<script src="{pre}assets/app.js"></script></body></html>'''

def src_link(r, pre):
    return f'<a class="src" href="{esc(r["source_url"])}" rel="nofollow noopener" target="_blank" title="{esc(r["source_name"])}, {esc(r["source_date"])} ({esc(r["date_type"])})">source ↗</a>'

AMAZON_TAG = 'edgetokens-20'
# Amazon US product pages (ASIN) verified 2026-10-17: page fetched, title + brand match the exact product/RAM variant.
# ('dp', ASIN, product label) = real product page.  ('s', query) = tagged search fallback (no live, exact US listing found).
_PI8   = ('dp', 'B0CK2FCG1K', 'Raspberry Pi 5 8GB')                 # brand Raspberry Pi
_PI16  = ('dp', 'B0DSPYPKRG', 'Raspberry Pi 5 16GB')                # brand Raspberry Pi, SC1113
_HAT2  = ('dp', 'B0GXKV2F7B', 'Raspberry Pi AI HAT+ 2')             # brand Raspberry Pi
_NANO  = ('dp', 'B0BZJTQ5YP', 'Jetson Orin Nano Super Developer Kit')   # brand NVIDIA
_NX8   = ('s', 'NVIDIA Jetson Orin NX 8GB module')
_NX16  = ('s', 'NVIDIA Jetson Orin NX 16GB module')
_M5LLM = ('s', 'M5Stack LLM Module Kit AX630C')
AMAZON = {
    'Raspberry Pi 5 8GB': _PI8,
    'Raspberry Pi 5 8GB (per node)': _PI8,
    'Raspberry Pi 5 16GB': _PI16,
    'Raspberry Pi AI HAT+ 2 (add-on, needs a Pi 5)': _HAT2,
    'Raspberry Pi 5 + AI HAT+ 2 (as tested in paper)': _HAT2,
    'Jetson Orin Nano Super Developer Kit': _NANO,
    'Jetson Orin Nano Developer Kit (same hardware, original power mode)': _NANO,
    'Jetson AGX Orin Developer Kit': ('dp', 'B0BYGB3WV4', 'Jetson AGX Orin 64GB Developer Kit'),   # brand NVIDIA, sold by Amazon.com
    'Jetson AGX Thor Developer Kit': ('dp', 'B0FTM2LXSF', 'Jetson AGX Thor Developer Kit'),        # brand NVIDIA
    'Jetson Orin NX 8GB module': _NX8,
    'Jetson Orin NX 8GB module (Super mode)': _NX8,
    'Jetson Orin NX 16GB module': _NX16,
    'Jetson Orin NX 16GB module (Super mode)': _NX16,
    'Radxa ROCK 5B 8GB': ('s', 'Radxa ROCK 5B 8GB'),          # official listing B0D1TZHFQF is "Currently unavailable"
    'Radxa ROCK 5B+ 16GB': ('s', 'Radxa ROCK 5B+ 16GB'),      # official listing B0DDTPF958 is "Currently unavailable"
    'Indiedroid Nova + heatsink, fan, eMMC': ('s', 'Indiedroid Nova RK3588S'),
    'ODROID-M2 w/ case, 64GB eMMC': ('s', 'Hardkernel ODROID-M2'),
    'Radxa ROCK 4D 8GB': ('s', 'Radxa ROCK 4D 8GB'),          # Radxa's Amazon listing only offers the 6GB variant
    'M5Stack LLM Module Kit (AX630C)': _M5LLM,                # official listing B0FGJT7WKF is "Currently unavailable"
    'M5Stack Module LLM (as tested in paper)': _M5LLM,
    'M5Stack AI Pyramid (AX8850)': ('s', 'M5Stack AI Pyramid AX8850'),
    'M5Stack LLM8850 M.2 card (AX8850)': ('s', 'M5Stack LLM8850 AX8850'),
    'Arduino UNO Q 4GB': ('dp', 'B0GFN669S4', 'Arduino UNO Q 4GB'),   # brand Arduino, ABX00173
}
def amazon_link(name):
    """-> (url, is_product_page, product_label). Raw (unescaped) URL."""
    e = AMAZON.get(name)
    if e is None: raise KeyError(f'No Amazon mapping for board {name!r}: add it to AMAZON in build_site.py')
    if e[0] == 'dp': return f'https://www.amazon.com/dp/{e[1]}?tag={AMAZON_TAG}', True, e[2]
    return f'https://www.amazon.com/s?k={urllib.parse.quote_plus(e[1])}&tag={AMAZON_TAG}', False, e[1]
def aff_slot(plat, pre, label=None, name=None, cls='aff'):
    u, dp, _ = amazon_link(name)
    label = label or ('Buy on Amazon' if dp else 'Check price on Amazon')
    return f'<a class="{cls}" href="{esc(u)}" data-aff-slot="{esc(plat)}" target="_blank" rel="sponsored nofollow noopener">{esc(label)}</a>'

# Seeed Studio affiliate (sensecap_affiliate code). Product pages verified 200 + correct product on 2026-10-17.
SEEED_AFF = 'sensecap_affiliate=WwUWAV9&referring_service=link'
_S = 'https://www.seeedstudio.com/'
SEEED_URLS = {
    'Raspberry Pi 5 8GB': _S+'Raspberry-Pi-5-8GB-p-5810.html',
    'Raspberry Pi 5 8GB (per node)': _S+'Raspberry-Pi-5-8GB-p-5810.html',
    'Raspberry Pi 5 16GB': _S+'Raspberry-Pi-5-16GB-p-6319.html',
    'Raspberry Pi AI HAT+ 2 (add-on, needs a Pi 5)': _S+'Raspberry-Pi-Al-HAT-2-p-6648.html',
    'Raspberry Pi 5 + AI HAT+ 2 (as tested in paper)': _S+'Raspberry-Pi-Al-HAT-2-p-6648.html',
    'Jetson Orin Nano Super Developer Kit': _S+'NVIDIAr-Jetson-Orintm-Nano-Super-Developer-Kit-Bundle.html',
    'Jetson Orin Nano Developer Kit (same hardware, original power mode)': _S+'NVIDIAr-Jetson-Orintm-Nano-Super-Developer-Kit-Bundle.html',
    'Jetson AGX Orin Developer Kit': _S+'NVIDIAr-Jetson-AGX-Orintm-64GB-Developer-Kit-Bundle.html',
    'Jetson AGX Thor Developer Kit': _S+'NVIDIAr-Jetson-AGX-Thortm-Developer-Kit-Bundle.html',
    'Jetson Orin NX 8GB module': _S+'NVIDIA-Jetson-Orin-NX-Module-8GB-p-5523.html',
    'Jetson Orin NX 8GB module (Super mode)': _S+'NVIDIA-Jetson-Orin-NX-Module-8GB-p-5523.html',
    'Jetson Orin NX 16GB module': _S+'NVIDIA-Jetson-Orin-NX-Module-16GB-p-5524.html',
    'Jetson Orin NX 16GB module (Super mode)': _S+'NVIDIA-Jetson-Orin-NX-Module-16GB-p-5524.html',
}
SEEED_LABEL = {'Raspberry Pi 5 + AI HAT+ 2 (as tested in paper)': 'Raspberry Pi AI HAT+ 2', 'Jetson Orin Nano Developer Kit (same hardware, original power mode)': 'Jetson Orin Nano Super Developer Kit'}
def seeed_slot(plat, name, label='Buy at Seeed Studio', cls='aff seeed'):
    u = SEEED_URLS.get(name)
    if not u: return ''
    u += ('&' if '?' in u else '?') + SEEED_AFF
    return f'<a class="{cls}" href="{esc(u)}" data-aff-slot="seeed-{esc(plat)}" target="_blank" rel="sponsored nofollow noopener">{esc(label)}</a>'

def params_of(r):
    try: v = float(r['params_b'])
    except (ValueError, TypeError): return None
    return v/1000 if v > 100 else v   # e.g. "450" = 450M in the source data
SIZES = [('tiny','Under 1B'),('small','1–2B'),('mid','3–4B'),('large','6–9B'),('xl','10B+'),('na','Size not stated')]
SIZE_LABEL = dict(SIZES)
def size_of(r):
    v = params_of(r)
    if v is None: return 'na'
    if v <= 1.0: return 'tiny'
    if v <= 2.0: return 'small'
    if v <= 4.5: return 'mid'
    if v <= 9.5: return 'large'
    return 'xl'
def size_txt(r):
    v = params_of(r)
    if v is None: return '–'
    return (f'{int(round(v*1000))}M' if v < 1 else f'{fmt(v)}B')
def rt_family(rt):
    l = rt.lower()
    for k,v in (('rkllm','RKLLM'),('hailo-ollama','hailo-ollama'),('distributed-llama','distributed-llama'),('ollama','Ollama'),('mlc','MLC'),('stackflow','StackFlow'),('llama.cpp','llama.cpp')):
        if k in l: return v
    return 'Other / not stated'
for r in B: r['size'] = size_of(r); r['rtf'] = rt_family(r['runtime'])

def sub_board(r):
    return '' if r['board'].strip().lower() == SHORT[r['platform']].lower() else f'<div class="sub">{esc(r["board"])}</div>'
def rt_html(rt):
    m = re.match(r'^(.*?)\s*\((.+)\)\s*$', rt)
    return f'{esc(m.group(1))}<div class="sub">{esc(m.group(2))}</div>' if m and m.group(1) else esc(rt)
def table(rows, pre, show_board=True, show_model=True, limit=False):
    rows = sorted(rows, key=lambda r:-r['gen_tps'])
    mx = max([r['gen_tps'] for r in rows] or [1])
    h = [f'<div class="tablewrap"><table class="lb{" limit" if limit else ""}"><thead><tr>']
    cols = []
    if show_board: cols.append(('Board','text',''))
    if show_model: cols.append(('Model','text',''))
    cols += [('Size','num','n'),('Quant','text','hide-sm'),('Runtime','text',''),('Gen tok/s','num','n'),('Prompt tok/s','num','n hide-sm'),('TTFT ms','num','n hide-sm'),('Source','text','')]
    h += [f'<th data-type="{t}" class="{c}" scope="col" tabindex="0" aria-sort="none">{n}</th>' for n,t,c in cols]
    h.append('</tr></thead><tbody>')
    for r in rows:
        w = max(2, round(100*(r['gen_tps']/mx)**0.5))
        h.append(f'<tr data-board="{esc(r["platform"])}" data-size="{r["size"]}" data-rt="{esc(r["rtf"])}">')
        if show_board: h.append(f'<td class="c-board" data-label="Board"><a href="{pre}boards/{r["platform"]}/index.html">{esc(SHORT[r["platform"]])}</a>{sub_board(r)}</td>')
        if show_model: h.append(f'<td class="c-model" data-label="Model"><a href="{pre}can/{r["platform"]}/{r["model_slug"]}/index.html">{esc(r["model"])}</a>{" <span class=tag>VLM</span>" if r["model_type"]=="vlm" else ""}</td>')
        h.append(f'<td class="n" data-label="Size" data-v="{params_of(r) if params_of(r) is not None else -1}">{size_txt(r)}</td>')
        h.append(f'<td class="hide-sm" data-label="Quant"><code>{esc(r["quant"])}</code></td><td data-label="Runtime">{rt_html(r["runtime"])}</td>')
        h.append(f'<td class="n gen" data-label="Gen tok/s" data-v="{r["gen_tps"]}"><span class="num">{fmt(r["gen_tps"])}</span><span class="barwrap" aria-hidden="true"><span class="bar" style="width:{w}%"></span></span></td>')
        h.append(f'<td class="n hide-sm" data-label="Prompt tok/s" data-v="{r["prompt_tps"] or -1}">{r["prompt_tps"] or "–"}</td><td class="n hide-sm" data-label="TTFT ms" data-v="{r["ttft_ms"] or -1}">{r["ttft_ms"] or "–"}</td>')
        h.append(f'<td data-label="Source">{src_link(r,pre)}<div class="sub">{"" if r["date_type"]=="published" else esc(r["date_type"].split(" ")[0])+" "}{esc(r["source_date"])}</div></td></tr>')
    h.append('</tbody></table></div>')
    return ''.join(h)

def write(path, content):
    full = os.path.join(OUT, path); os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full,'w').write(content)

if os.path.exists(OUT): shutil.rmtree(OUT)
os.makedirs(os.path.join(OUT,'assets')); os.makedirs(os.path.join(OUT,'data'))
shutil.copy(os.path.join(ROOT,'scripts','style.css'), os.path.join(OUT,'assets','style.css'))
shutil.copy(os.path.join(ROOT,'scripts','app.js'), os.path.join(OUT,'assets','app.js'))
open(os.path.join(OUT,'assets','favicon.svg'),'w').write(FAVICON)
shutil.copy(os.path.join(ROOT,'data','benchmarks.csv'), os.path.join(OUT,'data','benchmarks.csv'))
shutil.copy(os.path.join(ROOT,'data','boards.csv'), os.path.join(OUT,'data','boards.csv'))

byp = collections.defaultdict(list); bypm = collections.defaultdict(list)
for r in B: byp[r['platform']].append(r); bypm[(r['platform'],r['model_slug'])].append(r)
prices = collections.defaultdict(list)
for b in BD: prices[b['platform']].append(b)
urls = []

def buy_buttons(plat, name, pre):
    return f'<span class="buy">{seeed_slot(plat,name)}{aff_slot(plat,pre,name=name)}</span>'

def price_html(plat, pre):
    out = []
    for b in prices.get(plat, []):
        if b['price']:
            out.append(f'<li><div class="pl"><b>{esc(b["board_name"])}</b><span class="price">${esc(b["price"])}</span></div><div class="sub">{esc(b["price_note"])} · <a href="{esc(b["price_source_url"])}" target="_blank" rel="nofollow noopener">price source ↗</a> ({esc(b["price_date"])})</div>{buy_buttons(plat,b["board_name"],pre)}</li>')
        else:
            out.append(f'<li><div class="pl"><b>{esc(b["board_name"])}</b><span class="price none">price not verified yet</span></div>{buy_buttons(plat,b["board_name"],pre)}</li>')
    return '<ul class="prices">'+''.join(out)+'</ul>' if out else '<p class="sub">No verified price yet.</p>'

# ---- price basis per run (only listed, sourced prices; never estimated) ----
BDN = {b['board_name']: b for b in BD if b['price']}
def _p(name): return BDN[name]
def price_for(r):
    """Return (total_usd, [board rows], basis note) for the hardware a run was measured on, or None."""
    p, bd = r['platform'], r['board']
    if p == 'rpi5':
        if '16GB' in bd or '15 GiB' in bd: parts, note = ['Raspberry Pi 5 16GB'], 'Source ran a 16GB Pi 5.'
        elif '8GB' in bd: parts, note = ['Raspberry Pi 5 8GB'], 'Source ran an 8GB Pi 5.'
        else: parts, note = ['Raspberry Pi 5 8GB'], 'Source did not state RAM; priced as the cheapest listed Pi 5 (8GB).'
    elif p == 'rpi5-cluster':
        m = re.match(r'(\d+)x', bd)
        if not m: return None
        n = int(m.group(1)); b = _p('Raspberry Pi 5 8GB (per node)')
        return (round(n*float(b['price']),2), [b]*n, f'{n} × Pi 5 8GB at the listed per-node price (switch and cables not included).')
    elif p == 'rpi5-ai-hat-plus-2':
        if 'host not stated' in bd: return None
        parts = ['Raspberry Pi 5 8GB','Raspberry Pi AI HAT+ 2 (add-on, needs a Pi 5)']
        note = 'Pi 5 8GB + AI HAT+ 2 listed prices added together.' + ('' if '8GB' in bd else ' Source did not state Pi RAM.')
    elif p in ('jetson-orin-nano-super','jetson-orin-nano'):
        parts, note = ['Jetson Orin Nano Super Developer Kit'], 'Same dev kit for both power modes.'
    elif p == 'jetson-agx-orin': parts, note = ['Jetson AGX Orin Developer Kit'], 'Dev kit list price.'
    elif p == 'jetson-agx-thor': parts, note = ['Jetson AGX Thor Developer Kit'], 'Dev kit list price.'
    elif p == 'rk3588':
        if 'Indiedroid' in bd: parts, note = ['Indiedroid Nova + heatsink, fan, eMMC'], 'Source ran this exact board.'
        elif 'ODROID' in bd: parts, note = ['ODROID-M2 w/ case, 64GB eMMC'], 'Source ran this board ("from" price).'
        else: parts, note = ['Radxa ROCK 5B+ 16GB'], 'Chip-level vendor benchmark; priced at the cheapest listed RK3588 board.'
    elif p == 'rk3576': parts, note = ['Radxa ROCK 4D 8GB'], 'Chip-level vendor benchmark; priced at the cheapest listed RK3576 board.'
    elif p == 'm5stack-module-llm': parts, note = ['M5Stack LLM Module Kit (AX630C)'], 'Kit regular price (out of stock when checked).'
    else: return None
    rows = [_p(x) for x in parts]
    return (round(sum(float(x['price']) for x in rows),2), rows, note)

def price_links(rows):
    seen, out = set(), []
    for b in rows:
        if b['board_name'] in seen: continue
        seen.add(b['board_name'])
        out.append(f'<a href="{esc(b["price_source_url"])}" target="_blank" rel="nofollow noopener" title="{esc(b["board_name"])}: ${esc(b["price"])}, {esc(b["price_note"])} ({esc(b["price_date"])})">price ↗</a>')
    return ' '.join(out)

def money(v): return f'${v:,.0f}' if abs(v-round(v))<0.005 else f'${v:,.2f}'

def platform_of_part(b): return b['platform']

nb = len(byp); nm = len(MODEL_NAME); ns = len(set(r['source_url'] for r in B))
best_by_p = sorted(((max(r['gen_tps'] for r in rs), p) for p,rs in byp.items()), reverse=True)
bopts = ''.join(f'<option value="{esc(p)}">{esc(SHORT[p])} ({len(byp[p])})</option>' for p in sorted(byp, key=lambda p:SHORT[p]))
scount = collections.Counter(r['size'] for r in B)
sopts = ''.join(f'<option value="{k}">{v} ({scount[k]})</option>' for k,v in SIZES if scount[k])
rcount = collections.Counter(r['rtf'] for r in B)
ropts = ''.join(f'<option value="{esc(k)}">{esc(k)} ({n})</option>' for k,n in sorted(rcount.items(), key=lambda x:(x[0].startswith('Other'), -x[1])))

# ---- boards index + board pages ----
def from_price(p):
    ps = [float(b['price']) for b in prices.get(p, []) if b['price']]
    return f'from {money(min(ps))}' if ps else 'price not verified'
cards = []
for best,p in best_by_p:
    rs = byp[p]; models = len(set(r['model_slug'] for r in rs))
    cards.append(f'<a class="card" href="{p}/index.html"><p class="t-eyebrow">{from_price(p)}</p><h3>{esc(P[p][1])}</h3><p>{esc(P[p][2])}</p><div class="meta"><span class="cbest"><b>{fmt(best)}</b> tok/s best</span><span><b>{len(rs)}</b> runs</span><span><b>{models}</b> models</span></div></a>')
write('boards/index.html', page(f'All boards | {SITE}','Every edge AI board in the EdgeTokens dataset.',
    '<section class="pagehead"><p class="eyebrow">Boards</p><h1 class="display">Every board. <span class="mute">Every run.</span></h1><p class="lede">Pick a board to see every measured model run, current prices and sources. Sorted by fastest measured run.</p></section><div class="cards reveal">'+''.join(cards)+'</div>','boards/',1,'boards')); urls.append('boards/')

def uniq(xs):
    out = []
    for x in xs:
        if x and x not in out: out.append(x)
    return out
def hero_buy_row(p):
    rows = prices.get(p, [])
    ranked = sorted(rows, key=lambda b:(not SEEED_URLS.get(b['board_name']), not b['price'], float(b['price'] or 0)))
    return ranked[0] if ranked else None
# ---- accessories / starter kits (catalog in scripts/accessories.py) ----
def acc_url(k):
    a = ACC[k]
    if a.get('asin'): return f'https://www.amazon.com/dp/{a["asin"]}?tag={AMAZON_TAG}', True
    return f'https://www.amazon.com/s?k={urllib.parse.quote_plus(a["search"])}&tag={AMAZON_TAG}', False
def acc_seeed(k):
    u = ACC[k].get('seeed')
    return (u + ('&' if '?' in u else '?') + SEEED_AFF) if u else None
def acc_buttons(k, slot):
    au, dp = acc_url(k); su = acc_seeed(k); out = []
    if su: out.append(f'<a class="aff seeed" href="{esc(su)}" data-aff-slot="seeed-acc-{esc(k)}-{esc(slot)}" target="_blank" rel="sponsored nofollow noopener">Buy at Seeed Studio</a>')
    out.append(f'<a class="aff" href="{esc(au)}" data-aff-slot="acc-{esc(k)}-{esc(slot)}" target="_blank" rel="sponsored nofollow noopener">{"Buy on Amazon" if dp else "Check price on Amazon"}</a>')
    return '<span class="buy">' + ''.join(out) + '</span>'
def acc_price_html(k):
    a = ACC[k]
    if a.get('price') is None: return ''
    return f'<span class="kprice">{money(a["price"])}</span>'
def src_a(u, text):
    """Citation link. Seeed citations carry the affiliate code (and are marked sponsored) so no plain retailer link leaks out."""
    if 'seeedstudio.com' in u:
        su = u + ('&' if '?' in u else '?') + SEEED_AFF
        return f'<a href="{esc(su)}" target="_blank" rel="sponsored nofollow noopener">Seeed: {text}</a>'
    return f'<a href="{esc(u)}" target="_blank" rel="nofollow noopener">{text}</a>'
def acc_price_note(k):
    a = ACC[k]
    if a.get('price') is None: return ''
    return f'<div class="sub">{money(a["price"])} at {esc(a["price_by"])}, price at time of writing ({SRC_DATE}) · {src_a(a["price_src"], "price source ↗")}</div>'
def acc_why(k):
    a = ACC[k]; src = f' <a href="{esc(a["why_src"])}" target="_blank" rel="nofollow noopener">source ↗</a>' if a.get('why_src') else ''
    return f'<p class="kwhy">{esc(a["why"])}{src}</p>'
def acc_li(k, slot, tag=''):
    a = ACC[k]
    return (f'<li class="kitem"><div class="pl"><b>{esc(a["name"])}</b>{acc_price_html(k)}</div>'
            f'{("<p class=ktag>"+esc(tag)+"</p>") if tag else ""}{acc_why(k)}{acc_price_note(k)}{acc_buttons(k, slot)}</li>')
SD = ['sd-samsung', 'sd-sandisk']
# Per board family: (heading note, [(row label, [acc keys], required)], INCLUDED key or None, host board rows)
KIT_FOR = {
 'rpi5': ('Everything a Raspberry Pi 5 needs to run Ollama, beyond the board itself.',
          [('Power', ['pi-psu'], True), ('Cooling', ['pi-cooler'], True), ('Storage (pick one)', SD, True),
           ('Optional: case', ['pi-case'], False), ('Optional: NVMe boot', ['pi-m2hat', 'ssd-2230'], False)], None, []),
 'rpi5-cluster': ('Per node: each Pi 5 in a cluster needs the same parts. Ethernet switch and cables are not listed.',
          [('Power (per node)', ['pi-psu'], True), ('Cooling (per node)', ['pi-cooler'], True), ('Storage (per node, pick one)', SD, True)], None, []),
 'rpi5-ai-hat-plus-2': ('The AI HAT+ 2 is an add-on, so you also need the Pi 5 and its basics.',
          [('Power', ['pi-psu'], True), ('Cooling', ['pi-cooler'], True), ('Storage (pick one)', SD, True)], 'hat2', ['Raspberry Pi 5 8GB']),
 'jetson-orin-nano-super': ('The dev kit is almost complete out of the box. Add storage.',
          [('Storage (pick one)', SD, True), ('Optional: NVMe SSD (M.2 2280 slot)', ['ssd-2280'], False)], 'jetson', []),
 'jetson-orin-nano': ('Same dev kit as the Super (Super mode is a JetPack 6.2 flash). Add storage.',
          [('Storage (pick one)', SD, True), ('Optional: NVMe SSD (M.2 2280 slot)', ['ssd-2280'], False)], 'jetson', []),
 'jetson-agx-orin': ('Boots from its built-in eMMC. An NVMe SSD gives you room for bigger models.',
          [('Optional: NVMe SSD', ['ssd-2280'], False)], 'agx-orin', []),
 'jetson-agx-thor': ('Ships ready to boot.', [], 'agx-thor', []),
 'rk3588': ('For the Radxa ROCK 5B / 5B+ (the RK3588 boards we list on Amazon). Radxa ships the boards bare.',
          [('Power', ['radxa-psu'], True), ('Cooling', ['radxa-heatsink'], True), ('Storage (pick one)', SD, True),
           ('Optional: NVMe SSD (M.2 2280)', ['ssd-2280'], False)], None, []),
 'arduino-uno-q': ('What Arduino says the UNO Q needs for power, plus the hub for desktop (SBC) use.',
          [('Power', ['usbc-psu-5v3a'], True), ('Optional: desktop mode', ['usbc-hub-pd'], False)], None, []),
 'm5stack-module-llm': ('The kit has its own storage, mic and speaker.', [('Optional: host controller', ['m5-cores3'], False)], 'm5', []),
}
KIT_BOARD = {'rpi5': ['Raspberry Pi 5 8GB'], 'rpi5-ai-hat-plus-2': ['Raspberry Pi 5 8GB', 'Raspberry Pi AI HAT+ 2 (add-on, needs a Pi 5)'],
             'jetson-orin-nano-super': ['Jetson Orin Nano Super Developer Kit'], 'jetson-orin-nano': ['Jetson Orin Nano Super Developer Kit'],
             'jetson-agx-orin': ['Jetson AGX Orin Developer Kit'], 'jetson-agx-thor': ['Jetson AGX Thor Developer Kit'],
             'rk3588': ['Radxa ROCK 5B+ 16GB'], 'm5stack-module-llm': ['M5Stack LLM Module Kit (AX630C)']}
def kit_total(board_names, rows):
    """Sum of sourced prices only: board(s) + each REQUIRED row's cheapest priced option. Returns (total, parts, unpriced)."""
    parts, unpriced, tot = [], [], 0.0
    for n in board_names:
        b = BDN.get(n)
        if b: tot += float(b['price']); parts.append((re.sub(r'\s*\(.*?\)', '', n), float(b['price']), b['price_source_url']))
        else: unpriced.append(n)
    for label, keys, req in rows:
        if not req: continue
        pr = [k for k in keys if ACC[k].get('price') is not None]
        if pr:
            k = min(pr, key=lambda k: ACC[k]['price']); tot += ACC[k]['price']; parts.append((ACC[k]['short'], ACC[k]['price'], ACC[k]['price_src']))
        else: unpriced.append(' / '.join(ACC[k]['short'] for k in keys))
    return round(tot, 2), parts, unpriced
def total_html(tot, parts, unpriced, label='Approximate kit total'):
    if not parts: return ''
    br = ' + '.join(f'{esc(n)} {src_a(u, money(v))}' for n, v, u in parts)
    miss = f' Not included (no price we could source): {esc(", ".join(unpriced))}.' if unpriced else ''
    return f'<div class="ktotal"><p class="hs-label">{label}</p><p class="ktot-n">≈ {money(tot)}</p><p class="sub">{br}. Sourced prices at time of writing; they change often, shipping and tax not included.{miss}</p></div>'
def kit_section(p, pre):
    spec = KIT_FOR.get(p)
    if not spec: return ''
    note, rows, inc, hosts = spec
    lis = []
    for n in hosts:
        lis.append(f'<li class="kitem"><div class="pl"><b>{esc(n)}</b>{("<span class=kprice>$"+esc(BDN[n]["price"])+"</span>") if n in BDN else ""}</div><p class="ktag">Host board</p><p class="kwhy">The AI HAT+ 2 sits on top of a Pi 5. Our runs used an 8GB Pi 5 unless noted.</p>{buy_buttons(p, n, pre)}</li>')
    for label, keys, req in rows:
        for k in keys: lis.append(acc_li(k, p, label))
    inc_html = ''
    if inc:
        t, u = INCLUDED[inc]
        inc_html = f'<p class="callout kinc"><b>Good to know:</b> {esc(t)} <a href="{esc(u)}" target="_blank" rel="nofollow noopener">source ↗</a></p>'
    tot = ''
    if p in KIT_BOARD:
        tt, parts, un = kit_total(KIT_BOARD[p], rows)
        tot = total_html(tt, parts, un, 'Board + required parts, approximate')
    lst = f'<ul class="prices kit">{"".join(lis)}</ul>' if lis else ''
    return (f'<section class="section reveal" id="kit" aria-labelledby="kit-h"><h2 class="display3" id="kit-h">What you need to get running.</h2>'
            f'<p class="lede sm">{esc(note)} <a href="{pre}kits/index.html">Compare complete starter kits <span aria-hidden="true">›</span></a></p>{inc_html}{lst}{tot}</section>')

for p,rs in byp.items():
    best = max(rs, key=lambda r:r['gen_tps'])
    ms = sorted(set(r['model_slug'] for r in rs), key=lambda m: MODEL_NAME[m].lower())
    links = ''.join(f'<a class="chip" href="../../can/{p}/{m}/index.html">{esc(MODEL_NAME[m])}</a>' for m in ms)
    brs = prices.get(p, [])
    chips = uniq(b['chip'] for b in brs); mems = uniq(b['memory'] for b in brs)
    specs = []
    if chips: specs.append(('Chip', ' / '.join(chips)))
    if mems:
        parts = [m.split(' ',1) for m in mems]
        if len(parts) > 1 and all(len(x)==2 for x in parts) and len({x[1] for x in parts}) == 1:
            specs.append(('Memory', ' / '.join(x[0] for x in parts) + ' ' + parts[0][1]))
        else: specs.append(('Memory', ' / '.join(mems)))
    specs.append(('Price', from_price(p).replace('from ','From ').replace('price not verified','Not verified')))
    specs += [('Runs', str(len(rs))), ('Models', str(len(ms))), ('Sources', str(len(set(r["source_url"] for r in rs))))]
    spec_html = ''.join(f'<div><dt>{k}</dt><dd>{esc(v)}</dd></div>' for k,v in specs)
    hb = hero_buy_row(p)
    hero_buy = ''
    if hb:
        hero_buy = f'<div class="ctas">{seeed_slot(p,hb["board_name"],cls="pill primary aff")}{aff_slot(p,"../../",name=hb["board_name"],cls="pill ghost aff")}</div><p class="buynote">For the {esc(re.sub(r"\s*\(.*?\)","",hb["board_name"]))}{(", listed at $"+esc(hb["price"])) if hb["price"] else ""}. <a href="#buy">All options</a>{' · <a href="#kit">What else you need</a>' if p in KIT_FOR else ''}</p>'
    body = f'''<nav class="crumb" aria-label="Breadcrumb"><a href="../index.html">Boards</a> <span aria-hidden="true">›</span> <span>{esc(SHORT[p])}</span></nav>
<section class="product"><div class="glow" aria-hidden="true"></div>
<h1 class="display">{esc(P[p][1])}</h1><p class="lede">{esc(P[p][2])}</p>
<div class="bignum"><p class="hs-label">Fastest measured run</p><p class="hs-num"><span class="grad">{fmt(best["gen_tps"])}</span><span class="hs-unit">tok/s</span></p>
<p class="cap">{esc(best["model"])} · <code>{esc(best["quant"])}</code> · {esc(best["runtime"])} · {src_link(best,"../../")}</p></div>
{hero_buy}</section>
<dl class="specs reveal">{spec_html}</dl>
<section class="section reveal" id="buy" aria-labelledby="buy-h"><h2 class="display3" id="buy-h">Where to buy.</h2>{price_html(p,"../../")}</section>
{kit_section(p,'../../')}
<section class="section reveal" aria-labelledby="runs-h"><h2 class="display3" id="runs-h">Every run on this board.</h2>{table(rs,"../../",show_board=False)}</section>
<section class="section reveal" aria-labelledby="can-h"><h2 class="display3" id="can-h">Can the {esc(SHORT[p])} run…</h2><div class="chiprow wrapchips">{links}</div>
<p class="cta">Have this board? <a href="../../submit/index.html?board={p}">Submit your own run <span aria-hidden="true">›</span></a></p></section>'''
    write(f'boards/{p}/index.html', page(f'{P[p][1]} LLM benchmarks: tokens/sec for {len(ms)} models | {SITE}',
        f'Measured LLM speeds on the {P[p][1]}: {len(rs)} runs across {len(ms)} models, each with a source link.', body, f'boards/{p}/', 2, 'boards')); urls.append(f'boards/{p}/')

# ---- /value/: tokens per dollar ----
priced = [(r, price_for(r)) for r in B]
priced = [(r, pf) for r, pf in priced if pf]
cov = collections.defaultdict(set)
for r, pf in priced:
    if r['model_type'] == 'llm': cov[r['model_slug']].add(r['platform'])
VALUE_MODELS = [m for m,_ in sorted(cov.items(), key=lambda x:(-len(x[1]), MODEL_NAME[x[0]]))][:6]
def best_value(m):
    best = {}
    for r, pf in priced:
        if r['model_slug'] != m: continue
        v = r['gen_tps'] / pf[0] * 100
        if r['platform'] not in best or v > best[r['platform']][0]: best[r['platform']] = (v, r, pf)
    return sorted(best.values(), key=lambda x:-x[0])
tabs, panels = [], []
for i, m in enumerate(VALUE_MODELS):
    rows = best_value(m); mx = rows[0][0]
    tabs.append(f'<button type="button" class="seg" role="tab" data-tab="v-{m}" aria-selected="{"true" if i==0 else "false"}">{esc(MODEL_NAME[m])}</button>')
    trs = []
    for k, (v, r, pf) in enumerate(rows, 1):
        w = max(2, round(100*v/mx))
        trs.append(f'''<tr><td class="n rank" data-label="Rank">{k}</td>
<td class="c-board" data-label="Board"><a href="../boards/{r["platform"]}/index.html">{esc(SHORT[r["platform"]])}</a>{sub_board(r)}</td>
<td class="n" data-label="Best gen tok/s" data-v="{r["gen_tps"]}">{fmt(r["gen_tps"])} <span class="sub">{src_link(r,"../")}</span><div class="sub">{esc(r["runtime"])}, <code>{esc(r["quant"])}</code></div></td>
<td class="n" data-label="Price" data-v="{pf[0]}">{money(pf[0])} <span class="sub">{price_links(pf[1])}</span><div class="sub basis">{esc(pf[2])}</div></td>
<td class="n gen" data-label="tok/s per $100" data-v="{v:.4f}"><span class="num">{v:.2f}</span><span class="barwrap" aria-hidden="true"><span class="bar" style="width:{w}%"></span></span></td></tr>''')
    panels.append(f'''<section class="tabpanel" id="v-{m}" role="tabpanel" aria-label="{esc(MODEL_NAME[m])}"><div class="vlead"><p class="hs-label">{esc(MODEL_NAME[m])} · best value</p><p class="vlead-b">{esc(SHORT[rows[0][1]["platform"]])}</p><p class="hs-num sm"><span class="grad">{rows[0][0]:.2f}</span><span class="hs-unit">tok/s per $100</span></p><p class="cap">{len(rows)} priced boards ranked below.</p></div>
<div class="tablewrap"><table class="lb value"><thead><tr><th data-type="num" class="n" scope="col" tabindex="0">#</th><th data-type="text" scope="col" tabindex="0">Board</th><th data-type="num" class="n" scope="col" tabindex="0">Best gen tok/s</th><th data-type="num" class="n" scope="col" tabindex="0">Price</th><th data-type="num" class="n" scope="col" tabindex="0">tok/s per $100</th></tr></thead><tbody>{"".join(trs)}</tbody></table></div></section>''')
unpriced = sorted(SHORT[p] for p in byp if not any(price_for(r) for r in byp[p]))
value_body = f'''<section class="pagehead"><p class="eyebrow">Tokens per dollar</p><h1 class="display">Most speed. <span class="grad">Per dollar.</span></h1>
<p class="lede">For each board with a listed price, we take its fastest <b>sourced</b> generation speed on a common model and divide by the board's listed price. Higher is better.</p></section>
<details class="callout"><summary><b>How this is computed</b></summary> tok/s per $100 = best measured gen tok/s ÷ listed USD price × 100. Both inputs are sourced (links in every row); the ratio is simple arithmetic on them, not an estimate. Prices are the listed prices in our <a href="../data/boards.csv" download>board price list</a> and change often. Power supply, storage, cooling and shipping are not included. Different sources use different settings, so treat close values as a tie.</details>
<div class="segwrap"><div class="segs" role="tablist" aria-label="Choose a model">{"".join(tabs)}</div></div>
{"".join(panels)}
<p class="sub">Not ranked (no verified price yet): {esc(", ".join(unpriced))}. Runs where the source did not state the host board (e.g. "Hailo-10H, host not stated") are left out.</p>
<p class="cta">Know a better price or a faster run? <a href="../submit/index.html">Submit it →</a></p>'''
write('value/index.html', page(f'Best tokens per dollar: edge AI boards ranked by tok/s per $100 | {SITE}',
    'Which small board gives the most LLM speed per dollar? Sourced tok/s divided by listed price for Raspberry Pi 5, Jetson Orin Nano, RK3588 and more.',
    value_body, 'value/', 1, 'value')); urls.append('value/')


# ---- index / leaderboard (after /value/ so the tiles can quote a real value leader) ----
top = max(B, key=lambda r:r['gen_tps'])
def best_on(p):
    rs = byp.get(p)
    return max(rs, key=lambda r:r['gen_tps']) if rs else None
trio = ''.join(f'<li><span class="t-b">{esc(SHORT[p])}</span><span class="t-n">{fmt(r["gen_tps"])}<small> tok/s</small></span><span class="t-m">{esc(MODEL_NAME[r["model_slug"]])}</span></li>'
               for p in ('rpi5','jetson-orin-nano-super','rk3588') for r in [best_on(p)] if r)
hero = f'''<section class="hero"><p class="eyebrow">Open edge-AI benchmark database</p>
<h1 class="display">Real LLM speeds on small boards. <span class="grad">Every number sourced.</span></h1>
<p class="lede">Measured tokens per second on the Raspberry Pi, Jetson, Rockchip, Hailo and Axera boards makers actually buy. No estimates, no marketing math. Each result links to the public post, paper or log it came from.</p>
<div class="ctas"><a class="pill primary" href="#leaderboard">Explore the leaderboard</a><a class="pill ghost" href="pick/index.html">Which board should I buy? <span aria-hidden="true">›</span></a></div>
<figure class="herostat"><div class="glow" aria-hidden="true"></div>
<p class="hs-label">Fastest measured run in the database</p>
<p class="hs-num"><span class="grad">{fmt(top["gen_tps"])}</span><span class="hs-unit">tok/s</span></p>
<figcaption>{esc(top["model"])} on {esc(SHORT[top["platform"]])} · {esc(top["runtime"].split(" (")[0])} · {src_link(top,"")}</figcaption>
<ul class="trio" aria-label="Fastest measured run on popular boards">{trio}</ul></figure>
<dl class="stats"><div><dt>Measured runs</dt><dd>{len(B)}</dd></div><div><dt>Boards &amp; configs</dt><dd>{nb}</dd></div><div><dt>Models</dt><dd>{nm}</dd></div><div><dt>Public sources</dt><dd>{ns}</dd></div></dl></section>'''
vm = VALUE_MODELS[0]; vtop = best_value(vm)[0]
tiles = f'''<section class="section reveal" aria-labelledby="explore-h"><h2 class="display2" id="explore-h">Find the right board. <span class="mute">Without the guesswork.</span></h2>
<div class="tiles">
<a class="tile" href="pick/index.html"><p class="t-eyebrow">Board picker</p><h3>Which board should I buy?</h3><p>Set a budget and a model size. Get boards ranked by their fastest measured run.</p><span class="more">Open the picker <span aria-hidden="true">›</span></span></a>
<a class="tile" href="value/index.html"><p class="t-eyebrow">Best value</p><h3>Most speed per dollar.</h3><p>On {esc(MODEL_NAME[vm])}, the {esc(SHORT[vtop[1]["platform"]])} leads with <b class="gradtext">{vtop[0]:.2f}</b> tok/s per $100.</p><span class="more">See the ranking <span aria-hidden="true">›</span></span></a>
<a class="tile" href="boards/index.html"><p class="t-eyebrow">Boards</p><h3>{nb} boards &amp; configs.</h3><p>Every run, listed price and source for each board, from a Pi 5 to Jetson Thor.</p><span class="more">Browse boards <span aria-hidden="true">›</span></span></a>
</div></section>'''
controls = f'''<section class="section controls reveal" id="leaderboard" aria-labelledby="lb-h"><div class="ctl-head"><h2 class="display2" id="lb-h">The leaderboard.</h2><p class="sub" id="count" aria-live="polite">{len(B)} runs</p></div>
<div class="filters"><label class="f-q"><span class="vh">Search</span><svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><circle cx="11" cy="11" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M16 16l4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg><input id="q" type="search" placeholder="Search boards, models, runtimes" aria-label="Search board, model, runtime"></label>
<label><span class="vh">Board</span><select id="f-board" aria-label="Board"><option value="">All boards</option>{bopts}</select></label>
<label><span class="vh">Model size</span><select id="f-size" aria-label="Model size"><option value="">Any size</option>{sopts}</select></label>
<label><span class="vh">Runtime</span><select id="f-rt" aria-label="Runtime"><option value="">Any runtime</option>{ropts}</select></label>
<button class="pill ghost sm" type="button" id="clear">Reset</button></div>'''
note = '<div class="more-row"><button class="pill ghost" type="button" id="showall" hidden>Show all runs</button></div><p class="hint">Tap a column header to sort. <b>Gen tok/s</b> is generation (decode) speed. Sources use different prompts, runtimes and settings, so open the source before comparing two rows.</p></section>'
write('index.html', page(f'{SITE}: AI speed leaderboard for Raspberry Pi, Jetson, RK3588 & edge boards',
    'Measured LLM tokens/sec on Raspberry Pi 5, AI HAT+ 2, Jetson Orin Nano, RK3588 and more, with a source link on every number.',
    hero+tiles+controls+table(B,'',limit=True)+note, 'index.html', 0, 'home')); urls.insert(0,'')

# ---- /pick/: which board should I buy? ----
def buy_list(plat, parts):
    out, seen = [], set()
    multi = len({b['board_name'] for b in parts}) > 1
    for b in parts:
        n = b['board_name']
        if n in seen: continue
        seen.add(n)
        short = re.sub(r'\s*\(.*?\)', '', n)
        su = SEEED_URLS.get(n)
        if su: out.append({'l': ('Seeed: '+SEEED_LABEL.get(n, short)) if multi else 'Buy at Seeed Studio', 'u': su + ('&' if '?' in su else '?') + SEEED_AFF})
        au, adp, alab = amazon_link(n)
        out.append({'l': ('Amazon: '+(alab if adp else short)) if multi else ('Buy on Amazon' if adp else 'Check price on Amazon'), 'u': au})
    dd, seen_u = [], set()   # combos (e.g. Pi 5 + HAT) can map to the same product page; keep one button per URL
    for x in out:
        if x['u'] not in seen_u: seen_u.add(x['u']); dd.append(x)
    return dd
pick = []
for r, pf in priced:
    if r['model_type'] != 'llm' or r['size'] == 'na': continue
    pick.append({'p': r['platform'], 'b': SHORT[r['platform']], 'hw': r['board'], 'm': r['model'], 's': r['size'], 't': r['gen_tps'],
                 'rt': r['runtime'], 'q': r['quant'], 'src': r['source_url'], 'sn': r['source_name'], 'price': pf[0], 'basis': pf[2],
                 'buy': buy_list(r['platform'], pf[1])})
pick_json = json.dumps(pick, separators=(',',':')).replace('</', '<\\/')
budgets = [(100,'Under $100'),(150,'Up to $150'),(200,'Up to $200'),(400,'Up to $400'),(1000,'Up to $1,000'),(0,'No limit')]
bsel = ''.join(f'<button type="button" class="seg" data-budget="{v}" aria-pressed="{"true" if v==200 else "false"}">{t}</button>' for v,t in budgets)
pcount = collections.Counter(x['s'] for x in pick)
ssel = ''.join(f'<button type="button" class="seg" data-size="{k}" aria-pressed="{"true" if k=="mid" else "false"}">{v}</button>' for k,v in SIZES if pcount[k])
pick_body = f'''<section class="pagehead"><p class="eyebrow">Board picker</p><h1 class="display">Which board <span class="grad">should I buy?</span></h1>
<p class="lede">Pick a budget and the size of model you want to run. We rank the boards by the fastest <b>measured</b> speed in that size class, using only sourced runs and listed prices.</p></section>
<div class="picker"><div class="q"><h2 id="pkb-h">Budget</h2><div class="segwrap"><div class="segs" id="pk-budget" role="group" aria-labelledby="pkb-h">{bsel}</div></div></div>
<div class="q"><h2 id="pks-h">Model size</h2><div class="segwrap"><div class="segs" id="pk-size" role="group" aria-labelledby="pks-h">{ssel}</div></div><p class="sub">Examples: under 1B = Qwen2.5 0.5B; 1–2B = Qwen2.5 1.5B, Llama 3.2 1B; 3–4B = Llama 3.2 3B, Phi-3.5; 6–9B = Llama 3.1 8B, Qwen2.5 7B; 10B+ = Llama 2 13B.</p></div></div>
<div id="pk-out" aria-live="polite"><noscript><p class="callout">The picker needs JavaScript. You can still browse the <a href="../value/index.html">value ranking</a> or the <a href="../boards/index.html">board list</a>.</p></noscript></div>
<p class="sub">Speed shown is the best single sourced run for that board in the size class (generation tok/s). Prices are listed prices from our <a href="../data/boards.csv" download>price list</a>, not including PSU, storage or shipping. 10+ tok/s feels like chat, 4–10 is usable, under 4 is slow.</p>
<script type="application/json" id="pick-data">{pick_json}</script>'''
write('pick/index.html', page(f'Which board should I buy for local LLMs? Budget + model-size picker | {SITE}',
    'Choose a budget and model size and get edge AI board recommendations ranked by measured, sourced tokens/sec.',
    pick_body, 'pick/', 1, 'pick')); urls.append('pick/')

# ---- /kits/: best local-LLM starter kit per budget (board data + accessories, sourced prices only) ----
def runs_for(plat, m): return [r for r in byp.get(plat, []) if r['model_slug'] == m]
def best_run(plat, m):
    rs = runs_for(plat, m); return max(rs, key=lambda r: r['gen_tps']) if rs else None
def speed_line(plat, m, pre):
    rs = runs_for(plat, m)
    if not rs: return ''
    b = max(rs, key=lambda r: r['gen_tps']); lo = min(r['gen_tps'] for r in rs)
    rng = f' (range {fmt(lo)}–{fmt(b["gen_tps"])} across {len(rs)} runs)' if len(rs) > 1 and lo != b['gen_tps'] else ''
    return f'<li><span class="kspd"><b>{fmt(b["gen_tps"])}</b> tok/s</span> {esc(MODEL_NAME[m])} · {esc(b["runtime"])}, <code>{esc(b["quant"])}</code>{esc(rng)} · {src_link(b, pre)}</li>'
KITS = [
 dict(id='m5-llm', title='M5Stack LLM Module Kit', plat='m5stack-module-llm', boards=['M5Stack LLM Module Kit (AX630C)'],
      caveat='Out of stock at M5Stack when we checked. It runs models converted for its Axera NPU (M5Stack says off-the-shelf models cannot be used directly), and it is built to pair with an M5 host controller, which is not priced here.',
      cav_src='https://docs.m5stack.com/en/module/Module_LLM_Kit'),
 dict(id='rock5bp', title='Radxa ROCK 5B+ 16GB kit', plat='rk3588', boards=['Radxa ROCK 5B+ 16GB'],
      caveat='RK3588 speeds in our data run on the NPU through Rockchip\'s RKLLM, mostly from Rockchip\'s own reference-board benchmark, not a ROCK 5B+ specifically. Models must be converted to RKLLM format.',
      cav_src='https://github.com/airockchip/rknn-llm'),
 dict(id='pi5-8', title='Raspberry Pi 5 8GB kit', plat='rpi5', boards=['Raspberry Pi 5 8GB'],
      caveat='The easiest software path: Raspberry Pi OS plus Ollama. Everything runs on the CPU.', cav_src=None),
 dict(id='pi5-16', title='Raspberry Pi 5 16GB kit', plat='rpi5', boards=['Raspberry Pi 5 16GB'],
      caveat='Speeds shown are for the Pi 5 in general. In Jeff Geerling\'s tests the 16GB and 8GB boards ran Llama 3.1 8B at nearly the same speed; the extra RAM buys room for bigger models, not speed.',
      cav_src='https://github.com/geerlingguy/ai-benchmarks/issues/7'),
 dict(id='pi5-hat2', title='Raspberry Pi 5 + AI HAT+ 2 kit', plat='rpi5-ai-hat-plus-2', boards=['Raspberry Pi 5 8GB', 'Raspberry Pi AI HAT+ 2 (add-on, needs a Pi 5)'],
      caveat='The HAT runs Hailo-compiled models through hailo-ollama. In our sourced runs it generates more slowly than the Pi 5\'s own CPU on the same models, so read the sources before you buy it for LLM speed.', cav_src=None),
 dict(id='orin-nano', title='Jetson Orin Nano Super kit', plat='jetson-orin-nano-super', boards=['Jetson Orin Nano Super Developer Kit'],
      caveat='The power supply is in the box. The fastest numbers are NVIDIA\'s own MLC INT4 results; independent Ollama runs are much slower (see the range).',
      cav_src='https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/quick_start.html'),
]
for k in KITS:
    k['rows'] = KIT_FOR[k['plat']][1]
    k['total'], k['parts'], k['unpriced'] = kit_total(k['boards'], k['rows'])
def llm_models(plat): return {r['model_slug'] for r in byp.get(plat, []) if r['model_type'] == 'llm'}
def msize(m):
    v = [params_of(r) for r in B if r['model_slug'] == m and params_of(r) is not None]
    return max(v) if v else 0
def compare_model(kits):
    shared = set.intersection(*[llm_models(k['plat']) for k in kits]) if kits else set()
    return max(shared, key=lambda m: (msize(m), m)) if shared else None
TIERS = [(0, 150, 'under-150', 'Best local-LLM starter kit under $150'), (150, 250, 'under-250', 'Best local-LLM starter kit under $250'), (250, 500, 'under-500', 'Best local-LLM starter kit under $500')]
def kit_parts_html(k, pre):
    lis = []
    for n in k['boards']:
        lis.append(f'<li><div class="kp"><b>{esc(re.sub(r"\s*\(.*?\)","",n))}</b>{("<span class=kprice>"+money(float(BDN[n]["price"]))+"</span>") if n in BDN else ""}</div>{buy_buttons(k["plat"], n, pre)}</li>')
    for label, keys, req in k['rows']:
        for key in keys:
            a = ACC[key]
            lis.append(f'<li{"" if req else " class=opt"}><div class="kp"><span class="ktag">{esc(label)}</span><b>{esc(a["name"])}</b>{acc_price_html(key)}</div>{acc_buttons(key, "kit-"+k["id"])}</li>')
    inc = INCLUDED.get({'jetson-orin-nano-super': 'jetson', 'rpi5-ai-hat-plus-2': 'hat2', 'm5stack-module-llm': 'm5'}.get(k['plat'], ''), None)
    inc_html = f'<p class="sub kinc2">{esc(inc[0])} <a href="{esc(inc[1])}" target="_blank" rel="nofollow noopener">source ↗</a></p>' if inc else ''
    return f'<ul class="klist">{"".join(lis)}</ul>{inc_html}'
tier_html, tier_nav = [], []
for lo, hi, tid, ttl in TIERS:
    ks = [k for k in KITS if lo < k['total'] <= hi]
    cm = compare_model(ks)
    def keyf(k, cm=cm):
        b = best_run(k['plat'], cm) if cm else None
        return -(b['gen_tps'] if b else 0)
    ks.sort(key=lambda k: (keyf(k), k['total']))
    cards = []
    for i, k in enumerate(ks):
        models = uniq([cm, 'llama-3.2-3b', 'qwen2.5-1.5b'])
        sp = ''.join(speed_line(k['plat'], m, '../') for m in models if m)
        cav = f' <a href="{esc(k["cav_src"])}" target="_blank" rel="nofollow noopener">source ↗</a>' if k.get('cav_src') else ''
        cards.append(f'''<article class="kit-card{" top" if i == 0 else ""}">{'<div class="glow" aria-hidden="true"></div>' if i == 0 else ''}
<p class="t-eyebrow">{"Our pick" if i == 0 else "Also fits"}</p><h3>{esc(k["title"])}</h3>
<p class="ktot-n">≈ {money(k["total"])}</p><p class="sub">Board + required parts, sourced prices at time of writing{(", not including "+esc(", ".join(k["unpriced"]))) if k["unpriced"] else ""}.</p>
<ul class="kspeeds">{sp}</ul>
<p class="kwhy">{esc(k["caveat"])}{cav}</p>
{kit_parts_html(k, "../")}
<p class="cta"><a href="../boards/{k["plat"]}/index.html">All {esc(SHORT[k["plat"]])} runs <span aria-hidden="true">›</span></a></p></article>''')
    cmp_txt = (f'Ranked by the fastest sourced run on <b>{esc(MODEL_NAME[cm])}</b>, the largest model every kit in this tier has a measured result for.' if cm and len(ks) > 1 else
               'Only one kit in our data fits this budget with sourced prices.' if ks else 'No kit in our data fits this budget with sourced prices yet.')
    tier_nav.append(f'<a class="pill ghost sm" href="#{tid}">Under ${hi}</a>')
    tier_html.append(f'<section class="section reveal ktier" id="{tid}" aria-labelledby="{tid}-h"><h2 class="display3" id="{tid}-h">{esc(ttl)}.</h2><p class="sub">{cmp_txt}</p><div class="kit-cards">{"".join(cards)}</div></section>')
kits_body = f'''<section class="pagehead"><p class="eyebrow">Starter kits</p><h1 class="display">Everything you need. <span class="grad">Nothing you don't.</span></h1>
<p class="lede">Complete local-LLM starter kits at three budgets: a board from our data plus the power supply, cooling and storage it actually needs. Every speed links to its source, and every price is one we could source, so totals are approximate.</p>
<div class="ctas">{"".join(tier_nav)}</div></section>
{"".join(tier_html)}
<details class="callout"><summary><b>How we build these kits</b></summary> Board prices come from our <a href="../data/boards.csv" download>board price list</a>; accessory prices come from Seeed Studio, Samsung and Arace Tech product pages, checked {SRC_DATE}. We don't show Amazon prices, because they change hourly. A kit's total adds only prices we could source and lists anything left out. Speeds are the best single sourced run for that board family, and setups differ between sources, so open the source before you compare two boards closely. Some links are affiliate links (see below); they never change the ranking.</details>
<p class="cta">Have one of these boards? <a href="../submit/index.html">Submit your own run <span aria-hidden="true">›</span></a></p>'''
write('kits/index.html', page(f'Best local-LLM starter kits under $150, $250 and $500 | {SITE}',
    'Complete starter kits for running local LLMs on small boards: board, power, cooling and storage, with measured tokens/sec and sourced prices.',
    kits_body, 'kits/', 1, 'kits')); urls.append('kits/')

# ---- /guides/: short, data-backed buying + setup guides ----
def cell(plat, m, pre):
    b = best_run(plat, m)
    if not b: return '<td class="n" data-v="-1">–</td>'
    return f'<td class="n" data-v="{b["gen_tps"]}"><a href="{pre}can/{plat}/{m}/index.html">{fmt(b["gen_tps"])}</a></td>'
def ext(u, t='source ↗'): return f'<a href="{esc(u)}" target="_blank" rel="nofollow noopener">{t}</a>'
def gsec(title, inner, gid=''):
    return f'<section class="section reveal gsec"{(" id="+gid) if gid else ""}><h2 class="display3">{title}</h2>{inner}</section>'
def gpage(slug, title, desc, eyebrow, h1, lede, body):
    write(f'guides/{slug}/index.html', page(f'{title} | {SITE}', desc,
        f'<nav class="crumb" aria-label="Breadcrumb"><a href="../../kits/index.html">Starter kits</a> <span aria-hidden="true">›</span> <span>Guide</span></nav><section class="pagehead"><p class="eyebrow">{eyebrow}</p><h1 class="display2">{h1}</h1><p class="lede">{lede}</p><p class="sub">Updated {SRC_DATE}. Every speed links to its source; every price is sourced and dated.</p></section>{body}',
        f'guides/{slug}/', 2, 'kits')); urls.append(f'guides/{slug}/')
GP = '../../'
def pi(m): b = best_run('rpi5', m); return b['gen_tps'] if b else None
# 1) best board for local LLMs
GM = ['llama-3.2-1b', 'qwen2.5-1.5b', 'llama-3.2-3b', 'llama-3.1-8b']
GPLATS = ['rpi5', 'rpi5-ai-hat-plus-2', 'rk3588', 'jetson-orin-nano-super', 'jetson-agx-orin', 'm5stack-module-llm']
trs = ''.join(f'<tr><td class="c-board" data-label="Board"><a href="{GP}boards/{p}/index.html">{esc(SHORT[p])}</a><div class="sub">{from_price(p)}</div></td>' +
              ''.join(cell(p, m, GP).replace('<td class="n"', f'<td class="n" data-label="{esc(MODEL_NAME[m])}"', 1) for m in GM) + '</tr>' for p in GPLATS)
gtable = (f'<div class="tablewrap"><table class="lb guide-t"><thead><tr><th scope="col" data-type="text" tabindex="0">Board</th>' +
          ''.join(f'<th scope="col" class="n" data-type="num" tabindex="0">{esc(MODEL_NAME[m])}</th>' for m in GM) +
          f'</tr></thead><tbody>{trs}</tbody></table></div><p class="sub">Best sourced generation speed in tok/s; click a number for every run and its source. "–" means no sourced run yet. Prices are listed board prices from our <a href="{GP}data/boards.csv" download>price list</a>.</p>')
picks = []
for lo, hi, tid, ttl in TIERS:
    ks = sorted([k for k in KITS if lo < k['total'] <= hi], key=lambda k: (-(best_run(k['plat'], compare_model([x for x in KITS if lo < x['total'] <= hi])) or {'gen_tps': 0})['gen_tps'], k['total']))
    if ks:
        k = ks[0]
        picks.append(f'<li><b>Under ${hi}: {esc(k["title"])}</b> (≈ {money(k["total"])} for the board plus the parts it needs to run). <a href="{GP}kits/index.html#{tid}">See the full kit <span aria-hidden="true">›</span></a>{buy_buttons(k["plat"], k["boards"][-1], GP)}</li>')
orin3, pi3, hat3 = best_run('jetson-orin-nano-super', 'llama-3.2-3b'), best_run('rpi5', 'llama-3.2-3b'), best_run('rpi5-ai-hat-plus-2', 'llama-3.2-3b')
orin8, rk8, pi8 = best_run('jetson-orin-nano-super', 'llama-3.1-8b'), best_run('rk3588', 'llama-3.1-8b'), best_run('rpi5', 'llama-3.1-8b')
pq, rq = best_run('rpi5', 'qwen2.5-1.5b'), best_run('rk3588', 'qwen2.5-1.5b')
how = f'''<ul class="prose gl">
<li><b>Small models (1–2B) are fine on a Pi 5.</b> Its best sourced run on Qwen2.5 1.5B is {fmt(pq["gen_tps"])} tok/s ({src_link(pq, GP)}), above the 10 tok/s mark we treat as comfortable chat speed. An RK3588 board reached {fmt(rq["gen_tps"])} tok/s on the same model using its NPU ({src_link(rq, GP)}), but needs RKLLM-converted models.</li>
<li><b>3B models are where the Jetson pulls away.</b> On Llama 3.2 3B the Orin Nano Super's best is {fmt(orin3["gen_tps"])} tok/s ({src_link(orin3, GP)}) against {fmt(pi3["gen_tps"])} on a Pi 5 ({src_link(pi3, GP)}) and {fmt(hat3["gen_tps"])} on the AI HAT+ 2 ({src_link(hat3, GP)}).</li>
<li><b>8B models need a GPU or a lot of patience.</b> Llama 3.1 8B: {fmt(orin8["gen_tps"])} tok/s on the Orin Nano Super ({src_link(orin8, GP)}), {fmt(rk8["gen_tps"])} on RK3588 ({src_link(rk8, GP)}), {fmt(pi8["gen_tps"])} on a Pi 5 ({src_link(pi8, GP)}).</li>
<li><b>Count the extras.</b> A Pi 5 needs a power supply, a cooler and a microSD card; the Jetson includes its power supply. Each board page has a "What you need to get running" list, and the <a href="{GP}value/index.html">tokens-per-dollar ranking</a> shows which board gives the most speed per dollar.</li></ul>'''
gpage('best-board-for-local-llm', 'Best board for running a local LLM (2026): measured speeds and prices',
      'Which small board should you buy to run local LLMs? Measured tokens/sec on Raspberry Pi 5, AI HAT+ 2, RK3588 and Jetson Orin Nano Super, with sourced prices and complete starter kits.',
      'Buying guide', 'The best board for <span class="grad">local LLMs.</span>',
      'Short answer, by budget, then the numbers behind it. Every figure is a measured, sourced run from our database. No estimates.',
      gsec('The short answer.', f'<ul class="prose gl picks">{"".join(picks)}</ul>') +
      gsec('The numbers.', gtable) + gsec('How to choose.', how))
# 2) Raspberry Pi 5 local LLM setup
pi_rows = {}
for r in byp['rpi5']:
    if r['model_type'] == 'llm' and (r['model_slug'] not in pi_rows or r['gen_tps'] > pi_rows[r['model_slug']]['gen_tps']): pi_rows[r['model_slug']] = r
pi_best = sorted(pi_rows.values(), key=lambda r: -r['gen_tps'])
pi_tbl = table(pi_best, GP, show_board=False)
l1, q15, l3, l8 = best_run('rpi5', 'llama-3.2-1b'), pq, pi3, pi8
g8 = [r for r in byp['rpi5'] if r['model_slug'] == 'llama-3.1-8b']
g8txt = ', '.join(f'{fmt(r["gen_tps"])} tok/s on the {esc(r["board"].replace("Raspberry Pi 5 ", ""))} board' for r in sorted(g8, key=lambda r: r['board']))
pi_kit = ''.join(acc_li(k, 'guide-pi5', lab) for lab, keys, req in KIT_FOR['rpi5'][1] if req for k in keys)
pt, pparts, pun = kit_total(['Raspberry Pi 5 8GB'], KIT_FOR['rpi5'][1])
steps = f'''<ol class="prose gl steps">
<li><b>Flash Raspberry Pi OS (64-bit)</b> to the microSD card with Raspberry Pi Imager. {ext('https://www.raspberrypi.com/software/', 'Raspberry Pi Imager ↗')}</li>
<li><b>Fit the Active Cooler and plug in the 27W supply.</b> Boot, connect to your network and update: <code>sudo apt update &amp;&amp; sudo apt full-upgrade</code></li>
<li><b>Install Ollama</b> with its official Linux script: <pre><code>curl -fsSL https://ollama.com/install.sh | sh</code></pre> {ext('https://ollama.com/download/linux', 'Ollama Linux install ↗')}</li>
<li><b>Run a small model first.</b> <pre><code>ollama run llama3.2:1b --verbose</code></pre> <code>--verbose</code> prints the <i>eval rate</i> after each answer: that is your generation speed in tokens/sec.</li>
<li><b>Share your number.</b> Your run is exactly the kind of data this site is built on. <a href="{GP}submit/index.html?board=rpi5">Submit it here <span aria-hidden="true">›</span></a></li></ol>'''
expect = f'''<ul class="prose gl">
<li><b>1–2B models:</b> best sourced runs of {fmt(l1["gen_tps"])} tok/s on Llama 3.2 1B ({src_link(l1, GP)}) and {fmt(q15["gen_tps"])} tok/s on Qwen2.5 1.5B ({src_link(q15, GP)}). That is usable chat speed.</li>
<li><b>3B models:</b> {fmt(l3["gen_tps"])} tok/s best on Llama 3.2 3B ({src_link(l3, GP)}). Usable, but slower than you read.</li>
<li><b>8B models:</b> {fmt(l8["gen_tps"])} tok/s best on Llama 3.1 8B ({src_link(l8, GP)}). Jeff Geerling measured {g8txt}, so 16GB buys room for bigger models rather than speed.</li>
<li><b>Results vary a lot by setup.</b> One paper measured under 1 tok/s on the same models (see the full table below), so check the source before you compare.</li></ul>'''
gpage('raspberry-pi-5-local-llm-setup', 'Raspberry Pi 5 local LLM setup: what to buy, how to install Ollama, real speeds',
      'Run a local LLM on a Raspberry Pi 5: the parts you need, a 5-step Ollama setup, and measured tokens/sec for Llama 3.2, Qwen2.5 and more, every number sourced.',
      'Setup guide', 'Run a local LLM on a <span class="grad">Raspberry Pi 5.</span>',
      'What to buy, how to set it up in five steps, and what speed to expect, from real, sourced benchmark runs.',
      gsec('What to buy.', f'<p class="sub">An 8GB Pi 5 is enough for 1–3B models. Add these:</p><ul class="prices kit">{pi_kit}</ul>{total_html(pt, pparts, pun, "Pi 5 8GB + these parts, approximate")}<div class="ctas">{seeed_slot("rpi5", "Raspberry Pi 5 8GB", cls="pill primary aff")}{aff_slot("rpi5", GP, name="Raspberry Pi 5 8GB", cls="pill ghost aff")}</div><p class="sub">Want NVMe boot or a case? See the <a href="{GP}boards/rpi5/index.html#kit">full Pi 5 parts list</a>.</p>') +
      gsec('Set it up.', steps) + gsec('What speed to expect.', expect) +
      gsec('Every measured model on the Pi 5.', f'<p class="sub">Best sourced run per model.</p>{pi_tbl}'))
# 3) Jetson Orin Nano Super
NV = 'https://developer.nvidia.com/blog/nvidia-jetpack-6-2-brings-super-mode-to-nvidia-jetson-orin-nano-and-jetson-orin-nx-modules/'
pairs = []
for r in byp['jetson-orin-nano-super']:
    if r['source_url'] != NV: continue
    o = [x for x in byp['jetson-orin-nano'] if x['source_url'] == NV and x['model_slug'] == r['model_slug']]
    if o: pairs.append((r, o[0]))
pairs.sort(key=lambda x: -x[0]['gen_tps'])
ptr = ''.join(f'<tr><td data-label="Model">{esc(MODEL_NAME[s["model_slug"]])}</td><td class="n" data-label="Original mode" data-v="{o["gen_tps"]}">{fmt(o["gen_tps"])}</td><td class="n gen" data-label="Super mode" data-v="{s["gen_tps"]}"><span class="num">{fmt(s["gen_tps"])}</span></td><td class="n" data-label="Change" data-v="{s["gen_tps"]/o["gen_tps"]:.3f}">+{(s["gen_tps"]/o["gen_tps"]-1)*100:.0f}%</td></tr>' for s, o in pairs)
ptable = f'<div class="tablewrap"><table class="lb guide-t"><thead><tr><th scope="col" data-type="text" tabindex="0">Model (MLC, INT4)</th><th scope="col" class="n" data-type="num" tabindex="0">Original tok/s</th><th scope="col" class="n" data-type="num" tabindex="0">Super tok/s</th><th scope="col" class="n" data-type="num" tabindex="0">Change</th></tr></thead><tbody>{ptr}</tbody></table></div><p class="sub">Same hardware, same source: {ext(NV, "NVIDIA Technical Blog, JetPack 6.2 Super Mode ↗")}. The % change is simple arithmetic on the two sourced numbers.</p>'
ol = [r for r in byp['jetson-orin-nano-super'] if r['model_slug'] == 'llama-3.2-3b' and 'ollama' in r['runtime'].lower()]
olb = max(ol, key=lambda r: r['gen_tps']) if ol else None
j_kit = ''.join(acc_li(k, 'guide-orin', lab) for lab, keys, req in KIT_FOR['jetson-orin-nano-super'][1] for k in keys)
jt, jparts, jun = kit_total(['Jetson Orin Nano Super Developer Kit'], KIT_FOR['jetson-orin-nano-super'][1])
jinc = INCLUDED['jetson']
jsteps = f'''<ol class="prose gl steps">
<li><b>Flash JetPack</b> to a 64GB+ microSD card (or an NVMe SSD) using NVIDIA's quick start guide. Super mode arrived with JetPack 6.2. {ext('https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/quick_start.html', 'NVIDIA quick start ↗')}</li>
<li><b>Switch to the Super power mode</b> (MAXN SUPER) described in NVIDIA's announcement. {ext(NV, 'NVIDIA blog ↗')}</li>
<li><b>Pick a runtime.</b> NVIDIA's fastest numbers use MLC. Ollama is the easiest start and its Linux script supports Jetson: <pre><code>curl -fsSL https://ollama.com/install.sh | sh</code></pre> {ext('https://ollama.com/download/linux', 'Ollama Linux install ↗')}</li>
<li><b>Measure and share.</b> <code>ollama run llama3.2:3b --verbose</code> prints the eval rate. <a href="{GP}submit/index.html?board=jetson-orin-nano-super">Submit your run <span aria-hidden="true">›</span></a></li></ol>'''
jexp = f'<p class="sub">The runtime matters as much as the board: NVIDIA measured {fmt(orin3["gen_tps"])} tok/s on Llama 3.2 3B with MLC ({src_link(orin3, GP)})' + (f', while an independent Ollama test measured {fmt(olb["gen_tps"])} tok/s on the same model ({src_link(olb, GP)}).' if olb else '.') + '</p>'
gpage('jetson-orin-nano-super-local-llm', 'Jetson Orin Nano Super for local LLMs: Super mode speeds, what to buy, setup',
      'Jetson Orin Nano Super local LLM guide: measured Super vs original mode tokens/sec from NVIDIA, what to buy (power supply included), and how to get running.',
      'Setup guide', 'Jetson Orin Nano Super <span class="grad">for local LLMs.</span>',
      'Same board, a free software update, and a lot more speed. Here is what Super mode changes, what to buy, and how to start.',
      gsec('What Super mode changes.', ptable + jexp) +
      gsec('What to buy.', f'<p class="callout kinc"><b>Good to know:</b> {esc(jinc[0])} {ext(jinc[1])}</p><div class="ctas">{seeed_slot("jetson-orin-nano-super", "Jetson Orin Nano Super Developer Kit", cls="pill primary aff")}{aff_slot("jetson-orin-nano-super", GP, name="Jetson Orin Nano Super Developer Kit", cls="pill ghost aff")}</div><ul class="prices kit">{j_kit}</ul>{total_html(jt, jparts, jun, "Dev kit + microSD, approximate")}') +
      gsec('Set it up.', jsteps))

# ---- can-it-run pages ----
for (p,m),rs in bypm.items():
    best = max(r['gen_tps'] for r in rs); worst = min(r['gen_tps'] for r in rs)
    cls, vtxt = verdict(best)
    name = MODEL_NAME[m]; bn = SHORT[p]
    rng = f'{fmt(best)} tok/s' if best==worst else f'{fmt(worst)}–{fmt(best)} tok/s'
    others = sorted(((max(r['gen_tps'] for r in rr), pp) for (pp,mm),rr in bypm.items() if mm==m and pp!=p), reverse=True)[:6]
    oth = ''.join(f'<li><a href="../../{pp}/{m}/index.html">{esc(SHORT[pp])}</a> <b>{fmt(v)}</b> tok/s best</li>' for v,pp in others) or '<li class="sub">No other boards have this model yet.</li>'
    body = f'''<nav class="crumb" aria-label="Breadcrumb"><a href="../../../boards/index.html">Boards</a> <span aria-hidden="true">›</span> <a href="../../../boards/{p}/index.html">{esc(bn)}</a> <span aria-hidden="true">›</span> <span>{esc(name)}</span></nav>
<h1 class="display2">Can a {esc(bn)} run <span class="grad">{esc(name)}?</span></h1>
<div class="verdict {cls}"><span class="dot" aria-hidden="true"></span><b>{vtxt}.</b> Measured generation speed: <b>{rng}</b> across {len(rs)} public run{"s" if len(rs)>1 else ""}.</div>
<p class="sub">Rule of thumb: 10+ tok/s feels like a chat; 4–10 is usable for assistants and automations; under 4 is batch-job territory. Speeds depend on quantization, runtime, context length and cooling. Check each source.</p>
{table(rs,"../../../",show_board=True,show_model=False)}
<div class="grid2"><div class="panel"><h3>{esc(name)} on other boards</h3><ul class="kv">{oth}</ul></div>
<div class="panel"><h3>Buy a {esc(bn)}</h3>{price_html(p,"../../../")}</div></div>
<p class="cta">Ran {esc(name)} on a {esc(bn)}? <a href="../../../submit/index.html?board={p}&model={m}">Submit your numbers →</a></p>'''
    write(f'can/{p}/{m}/index.html', page(f'Can a {bn} run {name}? Measured: {rng} | {SITE}',
        f'Yes or no, with real numbers: {name} on the {bn} runs at {rng} (generation) across {len(rs)} sourced benchmark runs.', body, f'can/{p}/{m}/', 3, 'boards')); urls.append(f'can/{p}/{m}/')

# ---- submit ----
opts = ''.join(f'<option value="{p}">{esc(P[p][1])}</option>' for p in P) + '<option value="other">Other board (tell us below)</option>'
submit = f'''<section class="pagehead"><p class="eyebrow">Submit a run</p><h1 class="display">Share your <span class="grad">numbers.</span></h1><p class="lede">Ran a model on a small board? Send the numbers and a link to the log or post. We check every submission before it goes live and never publish a run without a source.</p></section>
<form class="sub-form" id="submit-form" onsubmit="return etSubmit(this)">
<p id="sub-ok" class="verdict yes" hidden>Almost done! We opened a pre-filled GitHub issue in a new tab. Click "Create" there to send your run. (No GitHub account? Email the same details to the newsletter address.)</p>
<label>Board<select name="board" required>{opts}</select></label>
<label>Accelerator / where it ran<input name="accelerator" placeholder="CPU, NPU, GPU, Hailo-10H…" required></label>
<label>Runtime + version<input name="runtime" placeholder="llama.cpp b6xxx, Ollama 0.x, RKLLM 1.3.1, MLC…" required></label>
<label>Model<input name="model" placeholder="Qwen2.5-3B-Instruct" required></label>
<label>Quantization<input name="quant" placeholder="Q4_K_M, w8a8, INT4…" required></label>
<div class="row"><label>Generation tok/s<input name="gen" type="number" step="0.01" required></label><label>Prompt tok/s (optional)<input name="pp" type="number" step="0.01"></label><label>TTFT ms (optional)<input name="ttft" type="number" step="1"></label></div>
<label>Source link (log, gist, post, video)<input name="url" type="url" required placeholder="https://"></label>
<label>Notes (power mode, cooling, context length…)<textarea name="notes" rows="3"></textarea></label>
<label>Email (optional, only to ask about your run)<input name="email" type="email"></label>
<button class="pill primary">Submit run</button></form>
<script>function etSubmit(f){{var d=new FormData(f),b=f.board.options[f.board.selectedIndex].text,L=[];
[['Board',b],['Accelerator',d.get('accelerator')],['Runtime + version',d.get('runtime')],['Model',d.get('model')],['Quantization',d.get('quant')],['Generation tok/s',d.get('gen')],['Prompt tok/s',d.get('pp')],['TTFT ms',d.get('ttft')],['Source',d.get('url')],['Notes',d.get('notes')],['Contact email',d.get('email')]].forEach(function(r){{if(r[1])L.push('**'+r[0]+':** '+r[1]);}});
var t='[Benchmark] '+d.get('model')+' on '+b+' ('+d.get('gen')+' tok/s)';
window.open('https://github.com/CharlesBuildsAI/edgetokens/issues/new?title='+encodeURIComponent(t)+'&body='+encodeURIComponent(L.join(String.fromCharCode(10,10))),'_blank');
document.getElementById('sub-ok').hidden=false;window.scrollTo(0,0);return false;}}</script>'''
write('submit/index.html', page(f'Submit a benchmark | {SITE}','Send us your edge AI benchmark run.', submit, 'submit/', 1, 'submit')); urls.append('submit/')

about = '''<section class="pagehead"><p class="eyebrow">Methodology</p><h1 class="display">How we <span class="grad">check.</span></h1></section><ul class="prose"><li><b>We only publish numbers someone actually measured</b> and published: vendor benchmark pages, papers, reviews, GitHub issues and community posts. Every row links to its source.</li>
<li><b>We don't estimate or extrapolate.</b> If a source gives a range or a "~", we record what it says and keep its wording in the notes.</li>
<li><b>Dates:</b> "published" means the source's publish date, "commit" a git commit date, "tested" the test date in the post, "accessed" when no date was shown (the date we read it).</li>
<li><b>Comparisons are approximate.</b> Prompt length, context, runtime version, power mode and cooling differ between sources.</li>
<li><b>Tokens per dollar:</b> the <a href="../value/index.html">value ranking</a> and <a href="../pick/index.html">board picker</a> divide a sourced speed by a sourced listed price. That is arithmetic on two sourced numbers, and every row links to both sources. Prices exclude PSU, storage, cooling and shipping.</li>
<li><b>Affiliate links:</b> some buy links may earn us a commission. They never change the numbers.</li></ul>'''
write('about/index.html', page(f'Methodology | {SITE}','How EdgeTokens collects and checks benchmark numbers.', about,'about/',1)); urls.append('about/')

write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{BASE_URL}/{u}</loc></url>' for u in urls)+'</urlset>')
write('robots.txt', f'User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n')
print(len(urls),'pages')
