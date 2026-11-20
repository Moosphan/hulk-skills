#!/usr/bin/env python3
"""出片审查：音画同步 / 时长 / 黑帧 / 响度。
用法: python3 qa_video.py <video.mp4> <timeline.json>
退出码 0 = PASS，1 = 有 FAIL。
"""
import json, re, subprocess, sys

def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return (p.stdout or '') + (p.stderr or '')

def main():
    video, tl_path = sys.argv[1], sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 else None
    tl = json.load(open(tl_path, encoding='utf-8'))
    total = float(tl['total']); cues = tl['cues']
    fails, warns = [], []

    dur = float(run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',video]).strip() or 0)
    if abs(dur - total) > 0.35:
        fails.append(f'时长 {dur:.2f}s 与时间轴 {total:.2f}s 相差 {abs(dur-total):.2f}s')

    # 语音起点
    src = voice or video
    sd = run(['ffmpeg','-hide_banner','-i',src,'-af','silencedetect=noise=-35dB:d=0.25','-f','null','-'])
    starts = [float(m) for m in re.findall(r'silence_end: ([0-9.]+)', sd)]
    if not starts:
        fails.append('没检测到语音段')
    drifts = []
    for c in cues:
        if not starts: break
        near = min(starts, key=lambda s: abs(s - c['start']))
        drifts.append(near - c['start'])
    if drifts:
        mx = max(drifts, key=abs)
        avg = sum(abs(d) for d in drifts)/len(drifts)
        print(f'语音起点漂移: 平均 {avg:.2f}s / 最大 {mx:+.2f}s（{len(drifts)} 句）')
        if abs(mx) > 0.45: fails.append(f'音画不同步：某句漂移 {mx:+.2f}s')
        elif abs(mx) > 0.25: warns.append(f'轻微不同步：{mx:+.2f}s')

    # 黑帧
    bd = run(['ffmpeg','-hide_banner','-i',video,'-vf','blackdetect=d=0.3:pic_th=0.98','-an','-f','null','-'])
    blacks = re.findall(r'black_start:([0-9.]+)', bd)
    if blacks: fails.append(f'检测到 {len(blacks)} 段黑帧（首段 {blacks[0]}s）')

    # 响度
    vd = run(['ffmpeg','-hide_banner','-i',video,'-af','volumedetect','-f','null','-'])
    mm = re.search(r'mean_volume: (-?[0-9.]+) dB', vd)
    if mm:
        mean = float(mm.group(1))
        print(f'平均响度: {mean} dB')
        if mean < -30: fails.append(f'整体过轻（{mean} dB）')

    print('---')
    for f in fails: print('FAIL', f)
    for w in warns: print('WARN', w)
    print('PASS' if not fails else 'FAILED')
    sys.exit(0 if not fails else 1)

if __name__ == '__main__':
    main()
