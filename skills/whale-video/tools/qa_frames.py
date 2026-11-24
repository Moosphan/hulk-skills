#!/usr/bin/env python3
"""版式抽检：按时间点抽帧拼成一张九宫格，供人眼检查叠加/安全区。
用法: python3 qa_frames.py <video.mp4> <out.jpg> [t1 t2 ...]
"""
import subprocess, sys, os, tempfile
video, out = sys.argv[1], sys.argv[2]
times = [float(x) for x in sys.argv[3:]] or [1, 8, 16, 24, 32, 40, 48, 56, 64]
tmp = tempfile.mkdtemp()
files = []
for i, t in enumerate(times[:9]):
    p = os.path.join(tmp, f"f{i}.jpg")
    subprocess.run(["ffmpeg","-v","error","-y","-ss",str(t),"-i",video,"-frames:v","1","-vf","scale=640:-1",p],check=True)
    files.append(p)
n = len(files)
cols = 3; rows = (n + 2)//3
args = []
for f in files: args += ["-i", f]
filt = "".join(f"[{i}:v]" for i in range(n))
filt += f"xstack=inputs={n}:layout=" + "|".join(
    f"{(i%3)*640}_{(i//3)*360}" for i in range(n)
) if n > 1 else ""
if n == 1:
    subprocess.run(["cp", files[0], out], check=True)
else:
    subprocess.run(["ffmpeg","-v","error","-y",*args,"-filter_complex",filt,out], check=True)
print(out)
