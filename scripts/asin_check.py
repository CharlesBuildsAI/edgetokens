#!/usr/bin/env python3
"""Fetch Amazon US product pages and print title / brand / availability (verification helper)."""
import sys, re, subprocess, html, os, time
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'
D=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','raw','asin')
def get(a):
    p=os.path.join(D,a+'.html')
    for i in range(3):
        r=subprocess.run(['curl','-s','-A',UA,'-H','Accept-Language: en-US,en;q=0.9','--compressed','-L','--max-time','30','-o',p,'-w','%{http_code}',f'https://www.amazon.com/dp/{a}'],capture_output=True,text=True).stdout
        s=open(p,errors='ignore').read() if os.path.exists(p) else ''
        if r=='200' and 'productTitle' in s: return r,s
        time.sleep(2)
    return r,s
for a in sys.argv[1:]:
    code,s=get(a)
    t=re.search(r'id="productTitle"[^>]*>(.*?)<',s,re.S); b=re.search(r'<a id="bylineInfo"[^>]*>(.*?)</a>',s,re.S)
    av=re.search(r'id="availability"[^>]*>.*?<span[^>]*>(.*?)</span>',s,re.S)
    pr=re.search(r'class="a-price aok-align-center[^"]*"[^>]*>.*?<span class="a-offscreen">(.*?)</span>',s,re.S) or re.search(r'id="corePrice_feature_div".*?<span class="a-offscreen">(.*?)</span>',s,re.S)
    f=lambda m: html.unescape(re.sub(r'\s+',' ',m.group(1))).strip() if m else None
    dv=re.search(r'"dimensionValuesDisplayData"\s*:\s*(\{.*?\})\s*,\s*"',s,re.S)
    if '-v' in os.environ.get('ASINV',''):
        print('   variants:', dv.group(1)[:1500] if dv else None)
    print(f'{a} {code} | {f(t)} | {f(b)} | avail={f(av)} | price={f(pr)}')
