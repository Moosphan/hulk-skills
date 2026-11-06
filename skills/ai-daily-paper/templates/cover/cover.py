#!/usr/bin/env python3
"""日报封面生成器（16:9 + 4:3 双版）
用法: python3 cover.py config.json
config: {
  "theme": "light|dark", "masthead": "AI 早报", "date": "2026 / 11 / 05",
  "account": "白音音的喵", "title": "会做动图了",
  "keywords": [{"text":"Images 2.6","style":"stroke"},{"text":"速度 +50%","style":"block"}],
  "sub": "OpenAI Images 2.6 · Flare / Sunburst",
  "logos": [{"path":"/tmp/logo-openai-dark.png","size":330},{"path":"/tmp/logo-claude2.png","size":210}],
  "cards": [["OpenAI","Images 2.6"],["Claude","Vault 结构"],["苹果","国行智能"]]
}
"""
import json, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SER='/System/Library/Fonts/Supplemental/Songti.ttc'
PIN='/System/Library/Fonts/PingFang.ttc'
S=4

def palette(theme):
    if theme == 'dark':
        return dict(bg=(20,16,12), ink=(242,231,213), sub=(168,156,140), accent=(232,145,45), spine=(178,58,46), card=(90,78,66))
    return dict(bg=(244,238,225), ink=(26,22,18), sub=(110,100,88), accent=(178,58,46), spine=(178,58,46), card=(150,136,118))

def sticker(logo, w, outline_color=(255,255,255), opacity=0.26, ol=49):
    pad0=int(w*0.24); h=int(logo.height*w/logo.width)
    lg=Image.new('RGBA',(w+pad0*2,h+pad0*2),(0,0,0,0))
    lg.alpha_composite(logo.resize((w,h),Image.LANCZOS),(pad0,pad0))
    a=lg.split()[-1]; outline=a.filter(ImageFilter.MaxFilter(ol))
    edge=Image.new('RGBA',lg.size,outline_color+(255,)); edge.putalpha(outline)
    sh=Image.new('RGBA',lg.size,(0,0,0,255)); sh.putalpha(outline.point(lambda v:int(v*opacity)))
    outer=int(w*0.18)+38; W,H=lg.width+outer*2,lg.height+outer*2
    shadow=Image.new('RGBA',(W,H),(0,0,0,0)); shadow.paste(sh,(outer+int(w*0.03),outer+int(w*0.035)),sh)
    shadow=shadow.filter(ImageFilter.GaussianBlur(int(w*0.035)))
    base=Image.new('RGBA',(W,H),(0,0,0,0)); base.alpha_composite(shadow)
    base.alpha_composite(edge,(outer,outer)); base.alpha_composite(lg,(outer,outer)); return base

def chip(d, text, x, y, fs, style, P):
    f=ImageFont.truetype(SER, fs*S)
    if style == 'block':
        tw=d.textlength(text,font=f)
        d.rectangle((x*S,y*S,x*S+tw+40*S,y*S+fs*S+34*S),fill=P['accent'])
        d.text((x*S+20*S,y*S+12*S),text,font=f,fill=(255,255,255))
        return tw/S+40
    d.text((x*S,y*S),text,font=f,fill=P['ink'],stroke_width=10,stroke_fill=(255,255,255) if P['bg'][0]>128 else (20,16,12))
    return d.textlength(text,font=f)/S

def build(cfg, W, H, out, sc_override=None):
    P=palette(cfg.get('theme','light')); sc=sc_override or W/1920.0
    im=Image.new('RGB',(W*S,H*S),P['bg']); d=ImageDraw.Draw(im)
    d.rectangle((0,0,16*S*sc,H*S),fill=P['spine'])
    d.text((96*S*sc,50*S*sc),cfg['masthead'],font=ImageFont.truetype(SER,int(54*S*sc)),fill=P['ink'])
    d.text((98*S*sc,118*S*sc),cfg['date'],font=ImageFont.truetype(PIN,int(26*S*sc),index=4),fill=P['sub'])
    nm=cfg['account']; fs=34*sc
    wnm=d.textlength(nm,font=ImageFont.truetype(PIN,int(fs*S),index=6))
    d.text((W*S-96*S*sc-wnm,56*S*sc),nm,font=ImageFont.truetype(PIN,int(fs*S),index=6),fill=P['ink'])
    d.ellipse((W*S-96*S*sc-wnm-20*S*sc,68*S*sc,W*S-96*S*sc-wnm-8*S*sc,80*S*sc),fill=P['accent'])
    d.text((92*S*sc,160*S*sc),cfg['title'],font=ImageFont.truetype(SER,int(170*S*sc)),fill=P['accent'])
    # 关键词：stroke 型号一行；block 数据点一行
    kws=cfg.get('keywords',[])
    stroke=[k for k in kws if k.get('style')!='block']
    blocks=[k for k in kws if k.get('style')=='block']
    if stroke:
        chip(d,stroke[0]['text'],96*sc,395*sc,96*sc,'stroke',P)
    bx=96*sc
    for k in blocks:
        f=ImageFont.truetype(SER,int(78*S*sc)); tw=d.textlength(k['text'],font=f)/S
        y=560*sc
        d.rectangle((bx*S,y*S,(bx+tw+40*sc)*S,(y+78*sc+30*sc)*S),fill=P['accent'])
        d.text((bx*S+20*S*sc,(y+12*sc)*S),k['text'],font=f,fill=(255,255,255))
        bx+=tw+70*sc
    d.text((98*S*sc,700*S*sc),cfg['sub'],font=ImageFont.truetype(PIN,int(32*S*sc),index=6),fill=P['sub'])
    # logos：右侧并排，右对齐；空间不够自动缩小
    logos=cfg.get('logos',[]); gap=int(40*S*sc); right=W*S-int(60*S*sc); minx=int(W*0.47*S)
    def mk(size):
        img=Image.open(logos[0 if len(sts)==0 else len(sts)]['path'] if False else '')
    sts=[]; sizes=[lg['size']*S*sc for lg in logos[:2]]
    total=sum(sizes)+ (len(sizes)-1)*gap*0 + 0
    # 先按原尺寸估算画布宽度
    def canvas_w(size, path):
        img=Image.open(path).convert('RGBA'); return sticker(img,int(size),outline_color=(255,255,255) if P['bg'][0]>128 else (28,22,16)).width
    widths=[canvas_w(sizes[i],logos[i]['path']) for i in range(len(sizes))]
    total=sum(widths)+gap*(len(widths)-1)
    allowed=right-minx
    if total>allowed:
        f=allowed/total
        widths=[int(w*f) for w in widths]
    y=int((H*0.14 if W>=1700 else H*0.56)*S*sc); x=right-sum(widths)-gap*(len(widths)-1)
    for i,lg in enumerate(logos[:2]):
        img=Image.open(lg['path']).convert('RGBA')
        st=sticker(img,int(lg['size']*S*sc*f) if total>allowed else int(lg['size']*S*sc),outline_color=(255,255,255) if P['bg'][0]>128 else (28,22,16))
        st=st.resize((widths[i], int(st.height*widths[i]/st.width)), Image.LANCZOS)
        im.paste(st,(x,y),st); x+=widths[i]+gap
    boxes=[]
    for st in sts:
        im.paste(st,(x,y),st)
        boxes.append((x/S,y/S,(x+st.width)/S,(y+st.height)/S))
        x+=st.width+gap
    for i in range(len(boxes)-1):
        a,b=boxes[i],boxes[i+1]
        if not (a[2]<=b[0] or b[2]<=a[0] or a[3]<=b[1] or b[3]<=a[1]):
            raise SystemExit(f'LOGO_OVERLAP {a} {b}')
    if boxes and boxes[-1][2] > W: raise SystemExit(f'LOGO_OVERFLOW {boxes[-1]}')

    cards=cfg.get('cards',[]); n=max(1,len(cards))
    gap=20*sc; margin=96*sc
    card_w=(W - margin*2 - gap*(n-1))/n
    cx=margin; card_top=H-200*sc
    for a,b in cards:
        d.rectangle((cx*S,card_top*S,(cx+card_w)*S,(card_top+125*sc)*S),outline=P['card'],width=2*S)
        d.text((cx*S+20*S*sc,(card_top+20*sc)*S),a,font=ImageFont.truetype(PIN,int(24*S*sc),index=6),fill=P['accent'])
        d.text((cx*S+20*S*sc,(card_top+62*sc)*S),b,font=ImageFont.truetype(PIN,int(32*S*sc),index=6),fill=P['ink'])
        cx+=card_w+gap
    im.resize((W,H),Image.LANCZOS).save(out,quality=95)

if __name__=='__main__':
    cfg=json.load(open(sys.argv[1]))
    out=cfg.get('out','/tmp/cover')
    build(cfg,1920,1080,f'{out}-169.jpg')
    cfg43=dict(cfg); cfg43['title']=cfg['title']
    build(cfg43,1440,1080,f'{out}-43.jpg',sc_override=0.86)
    print('ok', f'{out}-169.jpg', f'{out}-43.jpg')
