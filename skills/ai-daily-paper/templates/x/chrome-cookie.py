#!/usr/bin/env python3
"""从本机 Chrome 的 Cookie 库读 x.com 的 auth_token / ct0（macOS，需 Keychain 授权）。"""
import hashlib, os, shutil, sqlite3, subprocess, sys
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

PROFILE = os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Cookies")
TMP = "/tmp/chrome-cookies.db"

def key() -> bytes:
    pw = subprocess.run(["security", "find-generic-password", "-w", "-s", "Chrome Safe Storage", "-a", "Chrome"],
                        capture_output=True, text=True).stdout.strip()
    if not pw:
        sys.exit("拿不到 Keychain 里的 Chrome Safe Storage 密码")
    return hashlib.pbkdf2_hmac("sha1", pw.encode(), b"saltysalt", 1003, 16)

def decrypt(enc: bytes, k: bytes) -> str:
    if enc[:3] in (b"v10", b"v11"):
        enc = enc[3:]
    iv = b" " * 16
    d = Cipher(algorithms.AES(k), modes.CBC(iv)).decryptor()
    out = d.update(enc) + d.finalize()
    pad = out[-1]
    out = out[:-pad]
    # Chrome 127+ 会在明文前加 32 字节 host hash
    if len(out) > 32:
        tail = out[32:]
        if b'\x00' not in tail[:4] and all(32 <= b < 127 for b in tail[:8]):
            out = tail
    return out.decode("utf-8", "ignore")

def main():
    if not os.path.exists(PROFILE):
        sys.exit("找不到 Chrome Cookies 文件")
    shutil.copy2(PROFILE, TMP)
    con = sqlite3.connect(TMP)
    rows = con.execute(
        "select name, encrypted_value from cookies where host_key like '%x.com' and name in ('auth_token','ct0')"
    ).fetchall()
    if not rows:
        sys.exit("Chrome 里没有 x.com 的登录 cookie（先在 Chrome 登录小号）")
    k = key()
    out = {}
    for name, enc in rows:
        try:
            out[name] = decrypt(enc, k)
        except Exception as e:
            print(name, "decrypt failed", e, file=sys.stderr)
    for n, v in out.items():
        print(f"{n}={v[:12]}…({len(v)} chars)")
    if "auth_token" in out and "ct0" in out:
        import json
        open(os.path.expanduser("~/dsh-video-remotion/.x-cookies.json"), "w").write(
            json.dumps(out, indent=1))
        print("saved ~/dsh-video-remotion/.x-cookies.json")
    else:
        sys.exit("缺少 auth_token 或 ct0")

main()
