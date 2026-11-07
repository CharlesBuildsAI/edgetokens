"""Optional Chromium checks: uv run --no-project --with playwright python tests/browser_smoke.py."""
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT/'site')))
Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}'
checks=[]
def check(value, name):
    assert value,name
    checks.append(name)
try:
 with sync_playwright() as p:
    browser=p.chromium.launch(args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(base)
    check(page.locator('tbody tr:not([hidden])').count()==25,'initial 25 rows')
    page.locator('#f-source').select_option('independent')
    check(page.locator('tbody tr:not([hidden])').count()==21,'21 independent rows')
    page.locator('#f-model').select_option('llama-3.2-3b')
    n=page.locator('tbody tr:not([hidden])').count()
    check(n>0,'combined exact model and source filters')
    check(page.locator('tbody tr:not([hidden])').evaluate_all("rs=>rs.every(r=>r.dataset.source==='independent'&&r.dataset.model==='llama-3.2-3b')"),'visible rows match both filters')
    check('source=independent' in page.url and 'model=llama-3.2-3b' in page.url,'shareable query params')
    page.reload()
    check(page.locator('tbody tr:not([hidden])').count()==n,'filters survive reload')
    page.locator('tbody tr:not([hidden]) details summary').first.click()
    check(page.locator('tbody tr:not([hidden]) details').first.get_attribute('open') is not None,'run conditions expand')
    page.locator('#leaderboard').evaluate("el=>window.scrollTo(0,el.getBoundingClientRect().top+window.scrollY-64)")
    (ROOT/'preview').mkdir(exist_ok=True)
    page.wait_for_function("document.querySelector('#leaderboard').classList.contains('in')")
    page.wait_for_timeout(900)
    page.locator('#leaderboard').evaluate("el=>window.scrollTo(0,el.getBoundingClientRect().top+window.scrollY-80)")
    page.screenshot(path=str(ROOT/'preview/trust-desktop.png'))
    page.locator('#clear').click()
    check(page.locator('#f-model').input_value()=='' and page.locator('#f-source').input_value()=='','reset clears new filters')
    page.locator('#showall').click()
    check(page.locator('tbody tr:not([hidden])').count()==242,'show all 242 rows')
    page.locator('th').filter(has_text='Gen tok/s').first.click()
    check(page.locator('tbody tr:not([hidden])').count()==242,'sorting keeps rows')
    page.goto(base+'/pick/')
    page.evaluate("document.addEventListener('edgetokens:affiliate-click',e=>window.testClick=e.detail)")
    page.route('https://www.amazon.com/**',lambda route:route.abort())
    page.route('https://www.seeedstudio.com/**',lambda route:route.abort())
    page.locator('a[data-aff-slot]').first.click(no_wait_after=True)
    check(page.evaluate('window.testClick && !!window.testClick.merchant && !!window.testClick.slot'),'dynamic picker affiliate event')
    page.goto(base+'/submit/')
    check('will be public' in page.locator('label').filter(has_text='Contact email').inner_text(),'public email warning')
    page.set_viewport_size({'width':390,'height':844});page.goto(base+'/?source=vendor')
    check(page.locator('tbody tr:not([hidden])').count()==166,'mobile vendor filter')
    page.locator('#leaderboard').evaluate("el=>window.scrollTo(0,el.getBoundingClientRect().top+window.scrollY-64)")
    page.wait_for_function("document.querySelector('#leaderboard').classList.contains('in')")
    page.wait_for_timeout(900)
    page.locator('#leaderboard').evaluate("el=>window.scrollTo(0,el.getBoundingClientRect().top+window.scrollY-80)")
    page.screenshot(path=str(ROOT/'preview/trust-mobile.png'))
    check(page.evaluate('document.documentElement.scrollWidth<=window.innerWidth'),'mobile no page overflow')
    check(not errors,'no browser JS errors')
    print(f'{len(checks)} browser checks passed: '+', '.join(checks))
    browser.close()
finally:server.shutdown()
