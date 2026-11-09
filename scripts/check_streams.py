import concurrent.futures
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parent.parent
COUNTRIES = ROOT / "public" / "data" / "countries"
REPORT = ROOT / "public" / "data" / "stream-health.json"
MAX_WORKERS = 8
TIMEOUT_SECONDS = 8
PLAYLIST_BYTES = 16384
SEGMENT_BYTES = 1024
MAX_SEGMENTS_TO_CHECK = 2
MIN_REFRESH_WAIT_SECONDS = 6
MAX_REFRESH_WAIT_SECONDS = 21
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
    return sample


def read_url(url, byte_limit):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Range": f"bytes=0-{byte_limit - 1}",
            "Accept": "*/*",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return response.status, response.headers.get("Content-Type", "").lower(), response.read(byte_limit)
    except urllib.error.HTTPError as error:
        return error.code, error.headers.get("Content-Type", "").lower(), b""


def parse_media_playlist(body):
    lines = [line.strip() for line in body.decode("utf-8", errors="replace").splitlines()]
    media_sequence = 0
    target_duration = 6
    end_list = False
    segments = []

    for line in lines:
        if line.startswith("#EXT-X-MEDIA-SEQUENCE:"):
            try:
                media_sequence = int(line.split(":", 1)[1])
            except ValueError:
                pass
        elif line.startswith("#EXT-X-TARGETDURATION:"):
            try:
                target_duration = max(1, int(float(line.split(":", 1)[1])))
            except ValueError:
                pass
        elif line == "#EXT-X-ENDLIST":
            end_list = True
        elif line and not line.startswith("#"):
            segments.append(line)

    return {
        "media_sequence": media_sequence,
        "target_duration": target_duration,
        "end_list": end_list,
        "segments": segments,
    }


def load_media_playlist(url):
    status, content_type, body = read_url(url, PLAYLIST_BYTES)
    if not 200 <= status < 300 or not body.lstrip().startswith(b"#EXTM3U"):
        return status, content_type, url, None

    lines = [line.strip() for line in body.decode("utf-8", errors="replace").splitlines()]
    variant_uri = None
    for index, line in enumerate(lines):
        if line.startswith("#EXT-X-STREAM-INF"):
            variant_uri = next(
                (candidate for candidate in lines[index + 1:] if candidate and not candidate.startswith("#")),
                None,
            )
            break

    if variant_uri:
        media_url = urljoin(url, variant_uri)
        variant_status, variant_type, variant_body = read_url(media_url, PLAYLIST_BYTES)
        if not 200 <= variant_status < 300 or not variant_body.lstrip().startswith(b"#EXTM3U"):
            return variant_status, variant_type, media_url, None
        return variant_status, variant_type or content_type, media_url, parse_media_playlist(variant_body)

    return status, content_type, url, parse_media_playlist(body)


def check_latest_segments(media_url, playlist):
    segments = playlist["segments"][-MAX_SEGMENTS_TO_CHECK:]
    if not segments:
        return "unknown", "قائمة HLS موجودة لكن لم يظهر بها مقطع بث قابل للفحص"

    for segment_uri in segments:
        segment_url = urljoin(media_url, segment_uri)
        status, _, body = read_url(segment_url, SEGMENT_BYTES)
        if status in (404, 410):
            return "down", f"أحدث مقطع بث غير موجود (HTTP {status})"
        if not 200 <= status < 300 or not body:
            return "unknown", f"تعذر الوصول إلى أحد أحدث مقاطع البث (HTTP {status})"

    return "working", "تجددت قائمة HLS وتم الوصول إلى أحدث مقطعين"


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
        status, content_type, media_url, playlist = load_media_playlist(url)
        result["http_status"] = status
        result["content_type"] = content_type

        if status in (404, 410):
            result.update(status="down", message=f"قائمة البث غير موجودة (HTTP {status})")
            return result
        if not 200 <= status < 300 or playlist is None:
            result.update(message=f"تعذر التأكد من قائمة البث (HTTP {status})")
            return result

        if playlist["end_list"]:
            state, message = check_latest_segments(media_url, playlist)
            if state == "down":
                result.update(status=state, message=message)
            else:
                result.update(message="قائمة HLS منتهية؛ لا يمكن إثبات أن البث المباشر ما زال يتجدد")
            return result

        wait_seconds = min(
            max(playlist["target_duration"] * 2 + 1, MIN_REFRESH_WAIT_SECONDS),
            MAX_REFRESH_WAIT_SECONDS,
        )
        if playlist["target_duration"] * 2 + 1 > MAX_REFRESH_WAIT_SECONDS:
            result.update(message="فترة تحديث قائمة HLS طويلة؛ تعذر التحقق ضمن حد الانتظار الآمن")
            return result

        time.sleep(wait_seconds)
        second_status, second_type, second_media_url, second_playlist = load_media_playlist(media_url)
        if second_status in (404, 410):
            result.update(status="down", http_status=second_status, message=f"قائمة البث اختفت أثناء الفحص (HTTP {second_status})")
            return result
        if not 200 <= second_status < 300 or second_playlist is None:
            result.update(http_status=second_status, message=f"تعذر إعادة قراءة قائمة البث (HTTP {second_status})")
            return result

        first_last = playlist["segments"][-1] if playlist["segments"] else None
        second_last = second_playlist["segments"][-1] if second_playlist["segments"] else None
        advanced = (
            second_playlist["media_sequence"] > playlist["media_sequence"]
            or second_last != first_last
        )

        if not advanced:
            result.update(
                message=f"قائمة HLS لم تتجدد خلال {wait_seconds} ثانية؛ البث غير مؤكد"
            )
            return result

        state, message = check_latest_segments(second_media_url, second_playlist)
        if state == "working":
            result.update(status="working", content_type=second_type or content_type, message=message)
        elif state == "down":
            result.update(status="down", message=message)
        else:
            result.update(message=message)

    except Exception as error:
        result.update(message=f"تعذر الاتصال: {type(error).__name__}")
    return result


def main():
    sample = collect_sample()
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(check_stream, sample))
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_channels": len(sample),
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
        Stream health full scan: 
        f"{report['summary']['working']} working, "
        f"{report['summary']['down']} down, "
        f"{report['summary']['unknown']} unknown "
        f"({len(results)} checked)."
    )


if __name__ == "__main__":
    main()
