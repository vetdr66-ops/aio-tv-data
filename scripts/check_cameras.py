import concurrent.futures
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "cameras" / "global-index.json"
REPORT = ROOT / "public" / "cameras" / "health-report.json"

MAX_WORKERS = 16
TIMEOUT_SECONDS = 10
PLAYLIST_BYTES = 16384
MEDIA_BYTES = 2048
SEGMENT_BYTES = 1024
USER_AGENT = "AIO-TV-CameraHealth/1.0 (+https://github.com/vetdr66-ops/aio-tv-data)"


def fetch(url, byte_limit):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Range": f"bytes=0-{byte_limit - 1}",
            "Accept": "*/*",
            "Cache-Control": "no-cache",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return (
                response.status,
                response.headers.get("Content-Type", "").lower(),
                response.read(byte_limit),
            )
    except urllib.error.HTTPError as error:
        return error.code, error.headers.get("Content-Type", "").lower(), b""


def parse_hls_playlist(body):
    lines = [
        line.strip()
        for line in body.decode("utf-8", errors="replace").splitlines()
        if line.strip()
    ]
    if not lines or lines[0] != "#EXTM3U":
        return None, None

    for index, line in enumerate(lines):
        if line.startswith("#EXT-X-STREAM-INF:"):
            variant = next(
                (
                    candidate
                    for candidate in lines[index + 1:]
                    if not candidate.startswith("#")
                ),
                None,
            )
            return ("variant", variant) if variant else (None, None)

    segments = [line for line in lines if not line.startswith("#")]
    return "media", segments[-1] if segments else None


def result_base(camera, checked_at):
    return {
        "id": camera.get("id"),
        "name": camera.get("name"),
        "country": camera.get("country"),
        "country_name_ar": camera.get("country_name_ar"),
        "stream_type": camera.get("stream_type"),
        "source_family": camera.get("source_family"),
        "stream_url": camera.get("stream_url"),
        "source_last_verified": camera.get("last_verified"),
        "checked_at": checked_at,
        "status": "unknown",
        "http_status": None,
        "content_type": "",
        "message": "تعذر التحقق من البث",
    }


def check_hls(camera, result):
    url = camera["stream_url"]
    status, content_type, body = fetch(url, PLAYLIST_BYTES)
    result["http_status"] = status
    result["content_type"] = content_type

    if status in (404, 410):
        result.update(status="down", message=f"قائمة البث غير موجودة (HTTP {status})")
        return result
    if not 200 <= status < 300:
        result["message"] = f"تعذر الوصول إلى قائمة البث (HTTP {status})"
        return result

    playlist_type, target = parse_hls_playlist(body)
    if not playlist_type:
        result["message"] = "استجاب الرابط لكن محتوى HLS غير صالح أو بلا مقاطع"
        return result

    media_url = url
    if playlist_type == "variant":
        media_url = urljoin(url, target)
        status, variant_type, body = fetch(media_url, PLAYLIST_BYTES)
        if status in (404, 410):
            result["message"] = f"قائمة HLS الفرعية غير متاحة (HTTP {status})"
            return result
        if not 200 <= status < 300:
            result["message"] = f"تعذر الوصول إلى قائمة HLS الفرعية (HTTP {status})"
            return result
        _, segment = parse_hls_playlist(body)
        if not segment:
            result["message"] = "قائمة HLS الفرعية لا تحتوي على مقطع قابل للفحص"
            return result
        content_type = variant_type or content_type
    else:
        segment = target

    segment_url = urljoin(media_url, segment)
    segment_status, _, segment_body = fetch(segment_url, SEGMENT_BYTES)
    if 200 <= segment_status < 300 and segment_body:
        result.update(
            status="working",
            content_type=content_type,
            message="قائمة HLS وآخر مقطع متاحان"
        )
    else:
        result["message"] = (
            f"قائمة HLS متاحة لكن تعذر التحقق من آخر مقطع (HTTP {segment_status})"
        )
    return result


def check_mjpeg(camera, result):
    status, content_type, body = fetch(camera["stream_url"], MEDIA_BYTES)
    result["http_status"] = status
    result["content_type"] = content_type

    if status in (404, 410):
        result.update(status="down", message=f"رابط الكاميرا غير موجود (HTTP {status})")
    elif 200 <= status < 300 and body:
        is_mjpeg = (
            "multipart/x-mixed-replace" in content_type
            or "image/jpeg" in content_type
            or b"\xff\xd8" in body
        )
        if is_mjpeg:
            result.update(status="working", message="استجابة MJPEG وصورة JPEG متاحتان")
        else:
            result["message"] = "استجاب الرابط لكن نوع محتوى MJPEG غير مؤكد"
    else:
        result["message"] = f"تعذر التحقق من بث MJPEG (HTTP {status})"
    return result


def check_mp4(camera, result):
    status, content_type, body = fetch(camera["stream_url"], MEDIA_BYTES)
    result["http_status"] = status
    result["content_type"] = content_type

    if status in (404, 410):
        result.update(status="down", message=f"ملف الفيديو غير موجود (HTTP {status})")
    elif 200 <= status < 300 and body:
        is_mp4 = "video/mp4" in content_type or body[4:8] == b"ftyp"
        if is_mp4:
            result.update(status="working", message="ملف MP4 متاح للاستجابة")
        else:
            result["message"] = "استجاب الرابط لكن صيغة MP4 غير مؤكدة"
    else:
        result["message"] = f"تعذر التحقق من ملف MP4 (HTTP {status})"
    return result


def check_camera(camera):
    checked_at = datetime.now(timezone.utc).isoformat()
    result = result_base(camera, checked_at)
    url = camera.get("stream_url")
    stream_type = camera.get("stream_type")

    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        result["message"] = "رابط بث مفقود أو غير صالح"
        return result

    try:
        if stream_type == "hls":
            return check_hls(camera, result)
        if stream_type == "mjpeg":
            return check_mjpeg(camera, result)
        if stream_type == "mp4":
            return check_mp4(camera, result)
        result["message"] = f"نوع بث غير مدعوم: {stream_type}"
    except Exception as error:
        result["message"] = f"تعذر الاتصال: {type(error).__name__}"

    return result


def main():
    with CATALOG.open("r", encoding="utf-8") as catalog_file:
        catalog = json.load(catalog_file)

    cameras = catalog.get("cameras")
    expected_count = catalog.get("total_cameras")
    if not isinstance(cameras, list) or not cameras:
        raise ValueError("Camera catalog is missing or empty")
    if expected_count is not None and expected_count != len(cameras):
        raise ValueError(
            f"Camera count mismatch: catalog={expected_count}, records={len(cameras)}"
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(check_camera, cameras))

    summary = {
        "working": sum(item["status"] == "working" for item in results),
        "down": sum(item["status"] == "down" for item in results),
        "unknown": sum(item["status"] == "unknown" for item in results),
    }
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_catalog": catalog.get("source_catalog"),
        "source_catalog_license": catalog.get("source_catalog_license"),
        "catalog_camera_count": len(cameras),
        "checked_count": len(results),
        "summary": summary,
        "policy": (
            "Diagnostic only. The source camera catalog and stream URLs are never "
            "modified. Only HTTP 404/410 on the primary camera URL is classified "
            "as down; access restrictions, rate limits, server errors and timeouts "
            "remain unknown."
        ),
        "results": results,
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "Camera health scan: "
        f"{summary['working']} working, {summary['down']} down, "
        f"{summary['unknown']} unknown ({len(results)} checked)."
    )


if __name__ == "__main__":
    main()
