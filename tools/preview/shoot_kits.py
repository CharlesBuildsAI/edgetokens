# Starter-kit preview: dark (site default) with the OS set to LIGHT, desktop + mobile, full page. Scrolls first so reveals fire.
from playwright.sync_api import sync_playwright
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BASE=os.environ.get('BASE','http://localhost:8766')
OUT=os.path.join(ROOT, 'preview', 'kits'); os.makedirs(OUT, exist_ok=True)
pages={'kits':'/kits/','board-rpi5':'/boards/rpi5/','guide-best-board':'/guides/best-board-for-local-llm/','guide-pi5-setup':'/guides/raspberry-pi-5-local-llm-setup/','guide-jetson':'/guides/jetson-orin-nano-super-local-llm/'}
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
            pg.goto(BASE+u,wait_until='networkidle'); pg.wait_for_timeout(800)
            theme=pg.evaluate('document.documentElement.dataset.theme')
            settle(pg)
            if k=='board-rpi5':
                pg.evaluate("document.getElementById('kit').scrollIntoView()"); pg.wait_for_timeout(600)
                pg.screenshot(path=f'{OUT}/{k}-kit-section-{wname}-dark.png')
                pg.evaluate('window.scrollTo(0,0)'); pg.wait_for_timeout(300)
            pg.screenshot(path=f'{OUT}/{k}-{wname}-dark.png',full_page=True)
            sw=pg.evaluate('document.documentElement.scrollWidth'); 
            if sw>w: errs.append(f'{k} {wname}: horizontal overflow {sw}>{w}')
            if theme!='dark': errs.append(f'{k} {wname}: theme={theme}')
        ctx.close()
    b.close()
print('errors:',errs)
