# Apple redesign preview: dark mode (site default) with the OS set to LIGHT, to prove dark wins. Scrolls first so reveals fire.
from playwright.sync_api import sync_playwright
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT=os.path.join(ROOT, 'preview', 'apple'); os.makedirs(OUT, exist_ok=True)
pages={'home':'/','pick':'/pick/','value':'/value/','board-rpi5':'/boards/rpi5/'}
errs=[]
def settle(pg):
    h=pg.evaluate('document.body.scrollHeight'); y=0
    while y<h:
        pg.mouse.wheel(0,600); y+=600; pg.wait_for_timeout(60); h=pg.evaluate('document.body.scrollHeight')
    pg.evaluate('window.scrollTo(0,0)'); pg.wait_for_timeout(1100)
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    for wname,w,h,mob in (('desktop',1280,800,False),('mobile',390,844,True)):
        ctx=b.new_context(viewport={'width':w,'height':h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob,color_scheme='light')
        pg=ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e))); pg.on('console',lambda m: errs.append(m.text) if m.type=='error' else None)
        for k,u in pages.items():
            pg.goto('http://localhost:8765'+u,wait_until='networkidle'); pg.wait_for_timeout(1200)
            if k=='home': pg.screenshot(path=f'{OUT}/home-top-{wname}.png')
            settle(pg)
            pg.screenshot(path=f'{OUT}/{k}-{wname}.png',full_page=True)
        ctx.close()
    b.close()
print('errors:',errs)
