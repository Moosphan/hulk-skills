#!/usr/bin/env node
// 官方模型页取材：node official-model-media.mjs <url> <outDir> [--shots 5] [--videos 3] [--clip 8]
// 输出：截图 shots/*.png + 视频 videos/*.mp4（已裁时长、静音）+ media.json
import { pathToFileURL } from 'node:url';
const PW_ROOT = process.env.PW_ROOT || `${process.env.HOME}/dsh-video-remotion/news-video/node_modules`;
let pw;
try { pw = await import('playwright'); }
catch { pw = await import(pathToFileURL(`${PW_ROOT}/playwright/index.js`).href); }
const chromium = pw.chromium ?? pw.default?.chromium;
import { execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
const [,, url, outDir='./official-media'] = process.argv;
const shots = Number(process.argv.includes('--shots') ? process.argv[process.argv.indexOf('--shots')+1] : 5);
const vidsN = Number(process.argv.includes('--videos') ? process.argv[process.argv.indexOf('--videos')+1] : 3);
const clip = Number(process.argv.includes('--clip') ? process.argv[process.argv.indexOf('--clip')+1] : 8);
fs.mkdirSync(path.join(outDir,'shots'),{recursive:true});
fs.mkdirSync(path.join(outDir,'videos'),{recursive:true});
let proxy='';
try { const o=execSync('scutil --proxy').toString();
  const hp=(o.match(/HTTPSProxy\s*:\s*(\S+)/)||[])[1], pt=(o.match(/HTTPSPort\s*:\s*(\d+)/)||[])[1];
  if(hp&&pt) proxy=`http://${hp}:${pt}`; } catch {}
const b=await chromium.launch({proxy: proxy?{server:proxy}:undefined});
const p=await b.newPage({viewport:{width:1440,height:900},deviceScaleFactor:2,locale:'zh-CN'});
await p.goto(url,{waitUntil:'domcontentloaded',timeout:60000});
for(let i=0;i<15;i++){ await p.waitForTimeout(2500);
  const t=await p.innerText('body').catch(()=> '');
  const imgs=await p.evaluate(()=>document.querySelectorAll('img').length);
  if(!t.includes('Loading') && t.length>3000 && imgs>10) break; }
await p.waitForTimeout(1500);
const pageH=await p.evaluate(()=>document.body.scrollHeight);
const step=Math.max(600, Math.floor(pageH/shots));
for(let i=0;i<shots;i++){
  await p.evaluate(y=>window.scrollTo(0,y), i*step); await p.waitForTimeout(800);
  await p.screenshot({path:path.join(outDir,'shots',`sec-${i}.png`)});
}
const media=await p.evaluate(()=>({
  videos:Array.from(document.querySelectorAll('video')).map(v=>v.currentSrc||v.src).filter(Boolean),
  images:Array.from(document.querySelectorAll('img')).map(i=>i.src).filter(s=>s&&!s.startsWith('data:'))
}));
const picked=media.videos.slice(0,vidsN);
picked.forEach((u,i)=>{
  const out=path.join(outDir,'videos',`demo-${i}.mp4`);
  try{ execSync(`ffmpeg -y -v error -i "${u}" -t ${clip} -an -vf scale=1280:-2 -c:v libx264 -pix_fmt yuv420p -crf 20 "${out}"`); }catch(e){ console.error('video fail',i,e.message); }
});
fs.writeFileSync(path.join(outDir,'media.json'), JSON.stringify({url, media, picked},null,1));
await b.close();
console.log('done', outDir, 'videos', picked.length, 'shots', shots);
