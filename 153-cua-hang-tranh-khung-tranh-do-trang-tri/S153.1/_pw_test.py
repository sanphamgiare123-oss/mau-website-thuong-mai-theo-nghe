import json, os
from playwright.sync_api import sync_playwright

results = {}
errors = []
console_errors = []
url = 'file:///' + os.path.abspath('index.html').replace(os.sep, '/')
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 390, 'height': 844})
    pg.route('**://fonts.googleapis.com/**', lambda r: r.abort())
    pg.route('**://fonts.gstatic.com/**', lambda r: r.abort())
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.on('console', lambda m: console_errors.append(m.text) if m.type == 'error' else None)
    pg.goto(url, wait_until='domcontentloaded')
    pg.wait_for_timeout(1200)

    sw = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    results['overflow_top'] = sw

    pg.evaluate("document.getElementById('prodGrid').scrollIntoView()")
    pg.wait_for_timeout(600)
    pg.locator('[data-add]').first.click()
    pg.wait_for_timeout(500)
    results['badge'] = pg.evaluate("document.getElementById('cartBadge').textContent")
    results['badge_show'] = pg.evaluate("document.getElementById('cartBadge').classList.contains('show')")
    results['toast_count'] = pg.evaluate("document.querySelectorAll('#toastZone .toast').length")

    pg.evaluate("document.getElementById('dong-khung').scrollIntoView()")
    pg.wait_for_timeout(500)
    pg.click('#btnCfgAdd')
    pg.wait_for_timeout(500)
    results['badge_after_cfg'] = pg.evaluate("document.getElementById('cartBadge').textContent")
    pg.keyboard.press('Escape')
    pg.wait_for_timeout(600)

    pg.evaluate("document.getElementById('set-3-tranh').scrollIntoView()")
    pg.wait_for_timeout(500)
    pg.click('.btn-addkit[data-kit="giadinh"]')
    pg.wait_for_timeout(500)
    results['badge_after_set'] = pg.evaluate("document.getElementById('cartBadge').textContent")
    results['cart_total'] = pg.evaluate("document.getElementById('cdTotal') ? document.getElementById('cdTotal').textContent : 'n/a'")
    pg.keyboard.press('Escape')
    pg.wait_for_timeout(600)

    pg.evaluate("document.getElementById('hot').scrollIntoView()")
    pg.wait_for_timeout(400)
    pg.locator('[data-view]').first.click()
    pg.wait_for_timeout(500)
    results['qv_open'] = pg.evaluate("document.getElementById('qvBackdrop').classList.contains('show')")
    pg.keyboard.press('Escape')
    pg.wait_for_timeout(300)

    pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    pg.wait_for_timeout(1800)
    results['reveal_stuck'] = pg.evaluate("Array.from(document.querySelectorAll('.reveal')).filter(e=>!e.classList.contains('in')).length")
    results['overflow_bottom'] = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")

    pg.evaluate("document.getElementById('tu-van').scrollIntoView()")
    pg.wait_for_timeout(400)
    pg.click('#consultForm button[type="submit"]')
    pg.wait_for_timeout(400)
    results['form_toast'] = pg.evaluate("Array.from(document.querySelectorAll('#toastZone .toast b')).map(e=>e.textContent).slice(-1)")

    results['img_404'] = pg.evaluate("Array.from(document.images).filter(i=>i.complete && i.naturalWidth===0 && i.src).map(i=>i.src)")
    results['pageerrors'] = errors
    results['console_errors'] = console_errors[:5]

    # hero frame vs natural ratio check (bug #1: aspect distortion)
    pg.evaluate("window.scrollTo(0,0)")
    pg.wait_for_timeout(400)
    results['hero_ratio'] = pg.evaluate("""(() => {
      const img = document.querySelector('.hv-frame img');
      const r = img.getBoundingClientRect();
      return {display: (r.width/r.height).toFixed(3), natural: (img.naturalWidth/img.naturalHeight).toFixed(3)};
    })()""")

    b.close()
print(json.dumps(results, ensure_ascii=False, indent=1))
