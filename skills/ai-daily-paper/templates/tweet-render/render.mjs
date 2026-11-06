// 用法：node render.mjs <tweetId> <out.png>
// 依赖：playwright（在 news-video 目录下执行：cd ~/dsh-video-remotion/news-video && node <此文件>）
import { chromium } from 'playwright';
import fs from 'fs';
const id = process.argv[2];
const out = process.argv[3] || '/tmp/tweet.png';
const proxy = process.env.HTTPS_PROXY || process.env.https_proxy || 'http://127.0.0.1:7897';
const b = await chromium.launch({ proxy: { server: proxy, bypass: '127.0.0.1,localhost' } });
const p = await b.newPage({ viewport: { width: 900, height: 1400 }, deviceScaleFactor: 3 });
let ok = false;
for (let i = 0; i < 3 && !ok; i++) {
  await p.goto(`http://127.0.0.1:4399/?id=${id}`, { waitUntil: 'networkidle', timeout: 60000 });
  await p.waitForTimeout(2500);
  const t = await p.innerText('body');
  ok = !/Tweet not found|could not be found/i.test(t);
  if (!ok) console.log('retry', i + 1);
}
if (!ok) { await b.close(); throw new Error('TWEET_NOT_FOUND after retries'); }
await p.addStyleTag({ content: 'body{background:#fff}.react-tweet-theme{margin:0!important;border:1px solid #e1e8ed!important;border-radius:0!important} *{box-shadow:none!important;border-radius:0!important}' });
const buf = await p.locator('article').first().screenshot();
await b.close();
const sharp = null;
fs.writeFileSync(out, buf);
console.log('ok', out, buf.length);
