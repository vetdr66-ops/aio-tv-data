import concurrent.futures
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parent.parent
COUNTRIES = ROOT / "public" / "data" / "countries"
REPORT = ROOT / "public" / "data" / "stream-health.json"
SAMPLE_SIZE = 10
MAX_WORKERS = 2
TIMEOUT_SECONDS = 8
PLAYLIST_BYTES = 16384
SEGMENT_BYTES = 1024
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


def read_url(url, byte_limit):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Range": f"bytes=0-{byte_limit - 1}",
            "Accept": "*/*",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return response.status, response.headers.get("Content-Type", "").lower(), response.read(byte_limit)
    except urllib.error.HTTPError as error:
        return error.code, error.headers.get("Content-Type", "").lower(), b""


def first_playlist_uri(body):
    lines = [line.strip() for line in body.decode("utf-8", errors="replace").splitlines()]
    for index, line in enumerate(lines):
        if line.startswith("#EXT-X-STREAM-INF"):
            for candidate in lines[index + 1:]:
                if candidate and not candidate.startswith("#"):
                    return candidate
    for line in lines:
        if line and not line.startswith("#"):
            return line
    return None


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

    try:
        status, content_type, body = read_url(url, PLAYLIST_BYTES)
        result["http_status"] = status
        result["content_type"] = content_type

        if status in (404, 410):
            result.update(status="down", message=f"الرابط غير موجود (HTTP {status})")
            return result
        if not 200 <= status < 300:
            result.update(message=f"تعذر التأكد (HTTP {status})")
            return result

        looks_like_hls = (
            url.lower().split("?", 1)[0].endswith(".m3u8")
            or "mpegurl" in content_type
            or "vnd.apple.mpegurl" in content_type
            or body.lstrip().startswith(b"#EXTM3U")
        )

        if looks_like_hls:
            if not body.lstrip().startswith(b"#EXTM3U"):
                result.update(message="استجابة ناجحة لكن محتوى قائمة HLS غير واضح")
                return result

            media_url = url
            media_body = body
            variant_uri = None
            lines = [line.strip() for line in body.decode("utf-8", errors="replace").splitlines()]
            for index, line in enumerate(lines):
                if line.startswith("#EXT-X-STREAM-INF"):
                    variant_uri = next((candidate for candidate in lines[index + 1:] if candidate and not candidate.startswith("#")), None)
                    break

            if variant_uri:
                media_url = urljoin(url, variant_uri)
                variant_status, _, variant_body = read_url(media_url, PLAYLIST_BYTES)
                if variant_status in (404, 410):
                    result.update(status="down", message=f"قائمة البث الفرعية غير موجودة (HTTP {variant_status})")
                    return result
                if not 200 <= variant_status < 300 or not variant_body.lstrip().startswith(b"#EXTM3U"):
                    result.update(message=f"تعذر التحقق من قائمة البث الفرعية (HTTP {variant_status})")
                    return result
                media_body = variant_body

            segment_uri = first_playlist_uri(media_body)
            if not segment_uri:
                result.update(message="قائمة HLS موجودة لكن لم يظهر بها مقطع بث قابل للفحص")
                return result

            segment_url = urljoin(media_url, segment_uri)
            segment_status, segment_type, segment_body = read_url(segment_url, SEGMENT_BYTES)
            if segment_status in (404, 410):
                result.update(status="down", message=f"مقطع البث غير موجود (HTTP {segment_status})")
            elif 200 <= segment_status < 300 and segment_body:
                result.update(status="working", content_type=segment_type or content_type, message="قائمة HLS ومقطع بث واحد متاحان مبدئيًا")
            else:
                result.update(message=f"قائمة HLS موجودة لكن تعذر الوصول إلى مقطع البث (HTTP {segment_status})")
            return result

        if body and (
            content_type.startswith("video/")
            or "octet-stream" in content_type
            or "mp2t" in content_type
        ):
            result.update(status="working", message="استجابة وسائط ناجحة مبدئيًا")
        else:
            result.update(message="استجابة ناجحة لكن نوع المحتوى لا يثبت أنه بث")
    except Exception as error:
        result.update(message=f"تعذر الاتصال: {type(error).__name__}")
    return result


def main():
    sample = collect_sample()
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
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
