#!/usr/bin/env python3
"""海报版封面（同行对标，2026-11-06 定稿）
用法: python3 poster.py config.json
{
 "masthead":"AI 晚报","date":"26 / 11 / 06","account":"白音音的喵",
 "line1":"OpenAI","line2":"收购 Pierre","chip":"整合进 Codex",
 "logo_main":"/tmp/logo-openai-white.png","logo_second":"/tmp/logo-kimi.png",
 "tag":"",            // 可选文字标签，放在右下
 "out":"/tmp/cover"
}
"""
import json, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=4
SER='/System/Library/Fonts/Supplemental/Songti.ttc'; PIN='/System/Library/Fonts/PingFang.ttc'
THEMES={'dark':dict(INK=(242,231,213),ACC=(232,145,45),RED=(178,58,46),BG=(20,16,12),SUB=(168,156,140),BLUE=(88,166,255),EDGE=(255,255,255)),
        'light':dict(INK=(26,22,18),ACC=(178,58,46),RED=(178,58,46),BG=(244,238,225),SUB=(110,100,88),BLUE=(28,62,120),EDGE=(255,255,255))}

def sticker(path,w,op=0.26,ol=23):
    logo=Image.open(path).convert('RGBA'); pad=int(w*0.24); h=int(logo.height*w/logo.width)
    lg=Image.new('RGBA',(w+pad*2,h+pad*2),(0,0,0,0)); lg.alpha_composite(logo.resize((w,h),Image.LANCZOS),(pad,pad))
    a=lg.split()[-1]; out=a.filter(ImageFilter.MaxFilter(ol))
    edge=Image.new('RGBA',lg.size,(255,255,255,255)); edge.putalpha(out)
    sh=Image.new('RGBA',lg.size,(0,0,0,255)); sh.putalpha(out.point(lambda v:int(v*op)))
    o2=int(w*0.18)+38; W,H=lg.width+o2*2,lg.height+o2*2
    sd=Image.new('RGBA',(W,H),(0,0,0,0)); sd.paste(sh,(o2+int(w*0.03),o2+int(w*0.035)),sh); sd=sd.filter(ImageFilter.GaussianBlur(int(w*0.035)))
    base=Image.new('RGBA',(W,H),(0,0,0,0)); base.alpha_composite(sd); base.alpha_composite(edge,(o2,o2)); base.alpha_composite(lg,(o2,o2)); return base

def build(cfg,W,H,s,out):
    P=THEMES.get(cfg.get('theme','dark'),THEMES['dark'])
    global INK,ACC,RED,BG,SUB,BLUE
    INK,ACC,RED,BG,SUB,BLUE=P['INK'],P['ACC'],P['RED'],P['BG'],P['SUB'],P['BLUE']
    im=Image.new('RGB',(W*S,H*S),BG); d=ImageDraw.Draw(im); u=lambda v:int(v*S)
    d.rectangle((0,0,u(12),H*S),fill=RED)
    d.text((u(90),u(46)),cfg['date'],font=ImageFont.truetype(SER,u(46*s)),fill=BLUE)
    d.text((u(92),u(104)),f"{cfg['masthead']} · {cfg['account']}",font=ImageFont.truetype(PIN,u(24*s),index=6),fill=SUB)
    d.text((u(88),u(170)),cfg['line1'],font=ImageFont.truetype(SER,u(210*s)),fill=ACC)
    d.text((u(88),u(420)),cfg['line2'],font=ImageFont.truetype(SER,u(150*s)),fill=INK)
    f2=ImageFont.truetype(SER,u(84*s)); chip=cfg['chip']; tw=d.textlength(chip,font=f2)/S
    d.rectangle((u(90),u(640),u(90+tw+30),u(640+84*s+26)),fill=ACC)
    d.text((u(106),u(650)),chip,font=f2,fill=(255,255,255))
    t1=d.textlength(cfg['line1'],font=ImageFont.truetype(SER,u(210*s)))/S
    t2=d.textlength(cfg['line2'],font=ImageFont.truetype(SER,u(150*s)))/S
    text_right=88+max(t1,t2,tw+30)
    so,sk=580*s,320*s
    for _ in range(18):
        o=sticker(cfg['logo_main'],int(so*S)); k=sticker(cfg['logo_second'],int(sk*S))
        gap=u(28); total=o.width+k.width+gap; ox=W*S-u(60)-total
        if ox >= u(text_right+56): break
        so*=0.92; sk*=0.92
    else:
        raise SystemExit(f"LOGO_TOO_CLOSE text_right={text_right:.0f} logo_x={ox/S:.0f}")
    im.paste(o,(ox,u(110)),o); im.paste(k,(ox+o.width+gap,u(110)+int(o.height*0.55)),k)
    if cfg.get('tag'):
        tf=ImageFont.truetype(SER,u(46*s)); tag=cfg['tag']; tw2=d.textlength(tag,font=tf)/S
        tx=W-u(72)-tw2; ty=760
        d.rectangle((u(tx-26),u(ty-14),u(tx+tw2+26),u(ty+46*s+14)),outline=ACC,width=u(3))
        d.text((u(tx),u(ty)),tag,font=tf,fill=ACC)
    im.resize((W,H),Image.LANCZOS).save(out,quality=95)

if __name__=='__main__':
    c=json.load(open(sys.argv[1])); out=c.get('out','/tmp/poster')
    build(c,1920,1080,1.0,f'{out}-169.jpg'); build(c,1440,1080,0.95,f'{out}-43.jpg')
    print('ok',f'{out}-169.jpg',f'{out}-43.jpg')
