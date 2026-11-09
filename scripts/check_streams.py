import concurrent.futures
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
COUNTRIES = ROOT / "public" / "data" / "countries"
REPORT = ROOT / "public" / "data" / "stream-health.json"
SAMPLE_SIZE = 10
TIMEOUT_SECONDS = 12
USER_AGENT = "AIO-TV-StreamHealth/1.0 (+https://github.com/vetdr66-ops/aio-tv-data)"


def collect_sample():
    sample = []
    seen = set()
    for path in sorted(COUNTRIES.glob("*.json")):
        try:
            channels = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for channel in channels:
            channel_id = channel.get("id")
            streams = channel.get("streams") or []
            for stream in streams:
                url = stream if isinstance(stream, str) else stream.get("url")
                if not channel_id or not isinstance(url, str) or not url.startswith(("http://", "https://")):
                    continue
                if url in seen:
                    continue
                seen.add(url)
                sample.append({
                    "channel_id": channel_id,
                    "channel_name": channel.get("name") or channel_id,
                    "country": channel.get("country") or "",
                    "url": url,
                })
                break
            if len(sample) >= SAMPLE_SIZE:
                return sample
    return sample


def check_stream(item):
    url = item["url"]
    result = {
        "channel_id": item["channel_id"],
        "channel_name": item["channel_name"],
        "country": item["country"],
        "url": url,
        "host": urlparse(url).netloc,
        "status": "unknown",
        "http_status": None,
        "content_type": "",
        "message": "تعذر التحقق من الرابط",
    }
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Range": "bytes=0-4095",
            "Accept": "*/*",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            status = response.status
            content_type = response.headers.get("Content-Type", "").lower()
            body = response.read(4096)
            result["http_status"] = status
            result["content_type"] = content_type
            if status in (404, 410):
                result.update(status="down", message=f"الرابط غير موجود (HTTP {status})")
            elif 200 <= status < 300:
                looks_like_hls = (
                    url.lower().split("?", 1)[0].endswith(".m3u8")
                    or "mpegurl" in content_type
                    or "vnd.apple.mpegurl" in content_type
                )
                if looks_like_hls:
                    if body.lstrip().startswith(b"#EXTM3U"):
                        result.update(status="working", message="قائمة HLS سليمة مبدئيًا")
                    else:
                        result.update(status="unknown", message="استجابة HTTP ناجحة لكن محتوى HLS غير واضح")
                elif body and (
                    content_type.startswith("video/")
                    or "octet-stream" in content_type
                    or "mp2t" in content_type
                ):
                    result.update(status="working", message="استجابة وسائط ناجحة مبدئيًا")
                else:
                    result.update(status="unknown", message="استجابة ناجحة لكن نوع المحتوى لا يثبت أنه بث")
            else:
                result.update(status="unknown", message=f"استجابة HTTP غير حاسمة ({status})")
    except urllib.error.HTTPError as error:
        result["http_status"] = error.code
        if error.code in (404, 410):
            result.update(status="down", message=f"الرابط غير موجود (HTTP {error.code})")
        else:
            result.update(status="unknown", message=f"تعذر التأكد (HTTP {error.code})")
    except Exception as error:
        result.update(status="unknown", message=f"تعذر الاتصال: {type(error).__name__}")
    return result


def main():
    sample = collect_sample()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(check_stream, sample))
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sample_size": SAMPLE_SIZE,
        "checked_count": len(results),
        "policy": "Diagnostic only. No channel, stream URL, or override is changed.",
        "summary": {
            "working": sum(item["status"] == "working" for item in results),
            "down": sum(item["status"] == "down" for item in results),
            "unknown": sum(item["status"] == "unknown" for item in results),
        },
        "results": results,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "Stream health sample: "
        f"{report['summary']['working']} working, "
        f"{report['summary']['down']} down, "
        f"{report['summary']['unknown']} unknown "
        f"({len(results)} checked)."
    )


if __name__ == "__main__":
    main()
