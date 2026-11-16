#!/usr/bin/env node
// Capture a live chat.deepseek.com/share/... conversation as a standalone HTML
// export that tools/ds2md.py can convert.
//
// Share pages render the conversation through a virtualized list: the DOM only
// holds the rows near the viewport, so a naive fetch (curl is blocked outright
// by the WAF) or a save without scrolling yields a subset. This script scrolls
// the list to the end and harvests every mounted row on the way down, then
// writes one HTML file with the page <title> and og:url so the converter
// recovers the title and source link exactly as it would from a saved export.
//
// Usage:
//   node tools/fetch_share.js <share-url> -o /tmp/chat.html [--headful] [--timeout 180]
//
// Requires: Node 18+ and Playwright (see tools/README.md -> Setup).
// Exit codes: 0 captured, 1 failure (no messages / navigation error).

const fs = require('fs');
const path = require('path');

function parseArgs(argv) {
  const opts = { url: null, out: null, headful: false, timeout: 180 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '-o' || a === '--out') opts.out = argv[++i];
    else if (a === '--headful') opts.headful = true;
    else if (a === '--timeout') opts.timeout = Number(argv[++i]);
    else if (a === '-h' || a === '--help') {
      console.log('usage: node tools/fetch_share.js <share-url> -o <file.html> [--headful] [--timeout seconds]');
      process.exit(0);
    } else if (!opts.url) opts.url = a;
    else throw new Error(`unexpected argument: ${a}`);
  }
  if (!opts.url || !opts.out) throw new Error('both a share URL and -o <file.html> are required');
  return opts;
}

function browserUserAgent(browser) {
  // Playwright advertises "HeadlessChrome" by default, which the share page's
  // bot protection rejects. Present an ordinary desktop Chrome user agent.
  const major = browser.version().split('.')[0];
  return `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 ` +
         `(KHTML, like Gecko) Chrome/${major}.0.0.0 Safari/537.36`;
}

async function launch(chromium, headful) {
  const common = { headless: !headful, args: ['--disable-blink-features=AutomationControlled'] };
  try {
    // Prefer the installed Google Chrome: no bundled-browser download, and a
    // real Chrome build is less likely to be fingerprinted.
    return await chromium.launch({ channel: 'chrome', ...common });
  } catch (err) {
    console.warn(`warning: installed Chrome unavailable (${err.message.split('\n')[0]}); using bundled Chromium`);
    return await chromium.launch(common);
  }
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  const { chromium } = require('playwright');

  const browser = await launch(chromium, opts.headful);
  try {
    const context = await browser.newContext({
      viewport: { width: 1400, height: 1000 },
      locale: 'en-US',
      userAgent: browserUserAgent(browser),
    });
    const page = await context.newPage();
    await page.goto(opts.url, { waitUntil: 'domcontentloaded', timeout: opts.timeout * 1000 });

    try {
      await page.waitForSelector('[data-virtual-list-item-key]', { timeout: opts.timeout * 1000 });
    } catch (err) {
      const state = await page.evaluate(() => ({
        title: document.title,
        text: document.body.innerText.slice(0, 300),
      }));
      throw new Error(
        `no messages rendered (title: ${JSON.stringify(state.title)}). ` +
        `A bot challenge is the usual cause; retry with --headful and solve it in the window.\n` +
        `page text: ${JSON.stringify(state.text)}`
      );
    }
    await page.waitForTimeout(2500);

    const meta = await page.evaluate(() => {
      const og = (p) => document.querySelector(`meta[property="${p}"]`)?.content || '';
      return { title: document.title, ogUrl: og('og:url'), ogTitle: og('og:title'), ogDesc: og('og:description') };
    });

    const harvest = await page.evaluate(async () => {
      const sel = '[data-virtual-list-item-key]';
      const list = document.querySelector('.ds-virtual-list');
      let scroller = list;
      while (scroller && scroller !== document.body) {
        if (scroller.scrollHeight > scroller.clientHeight + 20) break;
        scroller = scroller.parentElement;
      }
      if (!scroller || scroller === document.body) {
        let el = document.querySelector(sel);
        const candidates = [];
        while (el) {
          if (el.scrollHeight > el.clientHeight + 20) candidates.push(el);
          el = el.parentElement;
        }
        scroller = candidates[candidates.length - 1] || document.scrollingElement;
      }

      const store = new Map();
      const grab = () => {
        for (const node of document.querySelectorAll(sel)) {
          const key = node.getAttribute('data-virtual-list-item-key');
          if (!store.has(key)) store.set(key, node.outerHTML);
        }
        return store.size;
      };

      grab();
      const step = 1400;
      let pos = 0;
      let reachedEnd = false;
      for (let guard = 0; guard < 4000; guard++) {
        const max = scroller.scrollHeight - scroller.clientHeight;
        if (pos >= max) { reachedEnd = true; break; }
        pos = Math.min(pos + step, max);
        scroller.scrollTop = pos;
        await new Promise((r) => setTimeout(r, 260));
        grab();
      }

      // Rows may still be settling at the bottom; keep working until a full
      // pass adds nothing, then sweep back up and harvest once more.
      let last = -1;
      let stable = 0;
      for (let pass = 0; pass < 6 && stable < 2; pass++) {
        scroller.scrollTop = scroller.scrollHeight;
        await new Promise((r) => setTimeout(r, 500));
        const n = grab();
        stable = n === last ? stable + 1 : 0;
        last = n;
      }
      for (let p = scroller.scrollHeight; p >= 0; p -= 1400) {
        scroller.scrollTop = p;
        await new Promise((r) => setTimeout(r, 180));
        grab();
      }
      scroller.scrollTop = 0;
      await new Promise((r) => setTimeout(r, 400));
      grab();

      const keys = [...store.keys()].map(Number).sort((a, b) => a - b);
      return {
        keys,
        reachedEnd: reachedEnd || scroller.scrollTop >= scroller.scrollHeight - scroller.clientHeight - 4,
        items: keys.map((k) => [k, store.get(String(k))]),
      };
    });

    if (!harvest.items.length) throw new Error('no message rows were captured');

    const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    const body = harvest.items.map(([k, html]) => `<!-- key ${k} -->\n${html}`).join('\n\n');
    const doc = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>${esc(meta.title)}</title>
<meta property="og:url" content="${esc(meta.ogUrl || opts.url)}">
<meta property="og:title" content="${esc(meta.ogTitle || meta.title)}">
<meta property="og:description" content="${esc(meta.ogDesc)}">
</head>
<body>
${body}
</body>
</html>
`;

    fs.mkdirSync(path.dirname(path.resolve(opts.out)), { recursive: true });
    fs.writeFileSync(opts.out, doc);

    const keys = harvest.keys;
    const positive = keys.filter((k) => k > 0);
    const missing = [];
    if (positive.length) {
      const present = new Set(positive);
      for (let k = positive[0]; k <= positive[positive.length - 1]; k++) {
        if (!present.has(k)) missing.push(k);
      }
    }

    console.log(`title:    ${meta.title}`);
    console.log(`source:   ${meta.ogUrl || opts.url}`);
    console.log(`messages: ${harvest.items.length} rows (keys ${keys[0]}..${keys[keys.length - 1]})`);
    if (keys.includes(-999)) console.log('banner:   AI-disclaimer row present (key -999, ignored by the converter)');
    if (missing.length) console.log(`gap keys: ${missing.join(', ')} (normal; ids of deleted rows)`);
    console.log(`complete: ${harvest.reachedEnd ? 'yes, scroll reached the end' : 'no, scroll stopped early — rerun before relying on the capture'}`);
    console.log(`wrote:    ${opts.out}`);
    console.log(`next:     /tmp/dsenv/bin/python tools/ds2md.py ${opts.out} -o notes/ --topic <topic> --title "..."`);
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error(`error: ${err.message}`);
  process.exit(1);
});
