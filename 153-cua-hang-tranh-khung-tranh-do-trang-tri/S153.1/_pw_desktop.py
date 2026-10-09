import json, os
from playwright.sync_api import sync_playwright

results = {}
url = 'file:///' + os.path.abspath('index.html').replace(os.sep, '/')
with sync_playwright() as p:
    b = p.chromium.launch()
    # ---------- DESKTOP 1280 ----------
    pg = b.new_page(viewport={'width': 1280, 'height': 800})
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**://fonts.googleapis.com/**', lambda r: r.abort())
    pg.route('**://fonts.gstatic.com/**', lambda r: r.abort())
    pg.goto(url, wait_until='domcontentloaded')
    pg.wait_for_timeout(1000)
    results['desktop_overflow'] = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")

    # khối-8: kín ô — từng hàng các thẻ phải liền mạch trái→phải, lấp full chiều rộng grid
    grid_info = pg.evaluate("""(() => {
      const grid = document.getElementById('prodGrid');
      const cards = Array.from(grid.querySelectorAll('.p-card'));
      const gr = grid.getBoundingClientRect();
      const rows = {};
      cards.forEach(c => {
        const r = c.getBoundingClientRect();
        const key = Math.round(r.top);
        rows[key] = rows[key] || [];
        rows[key].push({left: r.left, right: r.right, w: r.width, top: r.top, h: r.height});
      });
      const rowKeys = Object.keys(rows).sort((a,b)=>a-b);
      const gaps = [];
      rowKeys.forEach(k => {
        const items = rows[k].sort((a,b)=>a.left-b.left);
        let cursor = gr.left;
        items.forEach(it => {
          if (Math.abs(it.left - cursor) > 2) gaps.push({row:k, expectedLeft:cursor, actualLeft:it.left});
          cursor = it.right;
        });
        if (Math.abs(cursor - gr.right) > 2) gaps.push({row:k, rightEdgeGap: gr.right - cursor});
      });
      const widths = cards.map(c=>Math.round(c.getBoundingClientRect().width));
      return {n: cards.length, rows: rowKeys.length, gaps, gridW: Math.round(gr.width), widths};
    })()""")
    results['khoi8'] = grid_info

    # hero ratio desktop
    results['hero_ratio_desktop'] = pg.evaluate("""(() => {
      const img = document.querySelector('.hv-frame img');
      const r = img.getBoundingClientRect();
      return {display:(r.width/r.height).toFixed(3), natural:(img.naturalWidth/img.naturalHeight).toFixed(3)};
    })()""")

    # featured card rõ ràng to hơn: diện tích > 1.6x thẻ thường
    results['big_vs_normal'] = pg.evaluate("""(() => {
      const big = document.querySelector('.p-card.big').getBoundingClientRect();
      const normal = Array.from(document.querySelectorAll('#prodGrid .p-card:not(.big)'))[0].getBoundingClientRect();
      return {bigArea: Math.round(big.width*big.height), normArea: Math.round(normal.width*normal.height), ratio: (big.width*big.height/(normal.width*normal.height)).toFixed(2)};
    })()""")

    # search typeahead thật
    pg.fill('#searchInput', 'gương')
    pg.wait_for_timeout(400)
    results['search_hits'] = pg.evaluate("document.querySelectorAll('#searchDrop .sd-item').length")
    pg.fill('#searchInput', '')

    # đổi chất liệu trên thẻ đổi giá
    pg.evaluate("document.getElementById('hot').scrollIntoView()")
    pg.wait_for_timeout(400)
    results['mat_switch'] = pg.evaluate("""(() => {
      const card = document.querySelector('.p-card.big');
      const chips = card.querySelectorAll('.p-mat');
      chips[2].click();
      return card.querySelector('[data-mprice]').textContent;
    })()""")

    # cfg đổi size tự nhập → giá đổi
    pg.evaluate("document.getElementById('dong-khung').scrollIntoView()")
    pg.wait_for_timeout(400)
    pg.click('.cfg-size[data-w="custom"]')
    pg.fill('#cfgW', '70'); pg.fill('#cfgH', '100')
    pg.wait_for_timeout(300)
    results['cfg_custom_total'] = pg.evaluate("document.getElementById('cfgTotal').textContent")

    results['desktop_pageerrors'] = errs
    pg.close()

    # ---------- MOBILE re-check reveal ----------
    pg2 = b.new_page(viewport={'width': 390, 'height': 844})
    pg2.route('**://fonts.googleapis.com/**', lambda r: r.abort())
    pg2.route('**://fonts.gstatic.com/**', lambda r: r.abort())
    pg2.goto(url, wait_until='domcontentloaded')
    pg2.wait_for_timeout(1000)
    pg2.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    pg2.wait_for_timeout(1500)
    results['mobile_reveal_stuck'] = pg2.evaluate("Array.from(document.querySelectorAll('.reveal')).filter(e=>!e.classList.contains('in')).length")
    pg2.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
    pg2.wait_for_timeout(800)
    results['mobile_reveal_stuck_after_up'] = pg2.evaluate("Array.from(document.querySelectorAll('.reveal')).filter(e=>!e.classList.contains('in')).length")
    pg2.close()
    b.close()
print(json.dumps(results, ensure_ascii=False, indent=1))
