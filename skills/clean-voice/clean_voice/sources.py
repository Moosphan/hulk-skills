import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.bilibili.com/"}


def fetch_json(url):
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def checked_result(payload):
    if payload.get("code") != 0:
        raise ValueError(f"Bilibili access unavailable: {payload.get('message', payload.get('code'))}; provide an authorized local file if needed")
    return payload.get("result") or payload.get("data") or {}


def bilibili_audio_url(url, fetch=fetch_json):
    episode = re.search(r"/ep(\d+)", urllib.parse.urlparse(url).path)
    if episode:
        result = checked_result(fetch(f"https://api.bilibili.com/pgc/player/web/playurl?ep_id={episode.group(1)}&fnval=4048"))
    else:
        video = re.search(r"/(BV[0-9A-Za-z]+)", urllib.parse.urlparse(url).path)
        if not video:
            raise ValueError("Use a Bilibili BV video URL or bangumi /ep URL")
        detail = checked_result(fetch("https://api.bilibili.com/x/web-interface/view?bvid=" + video.group(1)))
        page_values = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get("p", ["1"])
        page = int(page_values[0])
        pages = detail.get("pages", [])
        if page < 1 or page > len(pages):
            raise ValueError("Requested Bilibili video part does not exist")
        cid = pages[page - 1]["cid"]
        result = checked_result(fetch(f"https://api.bilibili.com/x/player/playurl?bvid={video.group(1)}&cid={cid}&fnval=4048"))
    if result.get("is_drm") or result.get("is_preview"):
        raise ValueError("DRM or preview-only source; provide an authorized local file")
    audio = (result.get("dash") or {}).get("audio") or []
    if not audio:
        raise ValueError("No public audio stream available; provide a local file or use an explicitly authorized cookie file")
    best = max(audio, key=lambda entry: entry.get("bandwidth", 0))
    address = best.get("baseUrl") or best.get("base_url")
    if urllib.parse.urlparse(address or "").scheme not in ["http", "https"]:
        raise ValueError("Invalid audio stream URL")
    return address


def acquire(value, directory, runtime, cookies=None):
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in ["http", "https"]:
        path = Path(value).expanduser().resolve()
        if not path.is_file():
            raise ValueError(f"Input file is missing: {path}")
        return path
    host = parsed.hostname or ""
    if host in ["b23.tv", "www.b23.tv"]:
        request = urllib.request.Request(value, headers=HEADERS)
        with urllib.request.urlopen(request, timeout=30) as response:
            value = response.url
        host = urllib.parse.urlparse(value).hostname or ""
    if (host == "bilibili.com" or host.endswith(".bilibili.com")) and not cookies:
        address = bilibili_audio_url(value)
        target = directory / "download.m4a"
        request = urllib.request.Request(address, headers=HEADERS)
        with urllib.request.urlopen(request, timeout=45) as source, target.open("xb") as output:
            while True:
                block = source.read(1024 * 1024)
                if not block:
                    break
                output.write(block)
        return target
    result_path = directory / "download-result.json"
    runtime.worker("download", value, result_path, cookies=cookies, component="download")
    result = json.loads(result_path.read_text())
    path = Path(result["file"]).resolve()
    if not path.is_file() or not path.is_relative_to(directory.resolve()):
        raise ValueError("Downloader returned an invalid file")
    return path
