from playwright.sync_api import sync_playwright
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'preview')
os.makedirs(OUT, exist_ok=True)
pages={'home':'/','value':'/value/','pick':'/pick/','board-rpi5':'/boards/rpi5/'}
scheme = sys.argv[1] if len(sys.argv)>1 else 'light'
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    for wname,w,h,mob in (('desktop',1280,800,False),('mobile',390,844,True)):
        ctx=b.new_context(viewport={'width':w,'height':h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob,color_scheme=scheme)
        pg=ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e))); pg.on('console',lambda m: errs.append(m.text) if m.type=='error' else None)
        for k,u in pages.items():
            pg.goto('http://localhost:8765'+u,wait_until='networkidle')
            suf='' if scheme=='light' else '-dark'
            pg.screenshot(path=os.path.join(OUT, f'{k}-{wname}{suf}.png'), full_page=True)
        ctx.close()
    b.close()
print('errors:',errs)
