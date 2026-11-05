#!/usr/bin/env python3
"""Build a review-first VOD candidate index from Wikidata + Wikimedia Commons.

This script DOES NOT certify commercial rights. Every item remains blocked until
its Commons license and territorial public-domain status are reviewed manually.
"""
import html
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "public" / "vod" / "index.json"
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "AIO-TV-VOD-Catalog/0.1 (metadata indexing; rights review required)"
MIN_DURATION_SECONDS = 60 * 60
VIDEO_EXTENSIONS = (".webm", ".ogv", ".mp4", ".mkv", ".avi")
REQUEST_INTERVAL_SECONDS = 1.1
_LAST_REQUEST_AT = 0.0

QUERY = """
SELECT DISTINCT ?film ?filmLabel ?year ?video WHERE {
  ?film wdt:P31/wdt:P279* wd:Q11424;
        wdt:P10 ?video;
        wdt:P577 ?date.
  VALUES ?country { wd:Q668 wd:Q129286 }
  ?film wdt:P495 ?country.
  FILTER(YEAR(?date) < 1964)
  BIND(YEAR(?date) AS ?year)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,hi,bn,ta,te,ml,ur". }
}
ORDER BY ?filmLabel
"""


def fetch_json(url, params=None):
    global _LAST_REQUEST_AT
    if params:
        url = url + ("&" if "?" in url else "?") + urlencode(params)
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json, application/json"})
    for attempt in range(6):
        wait_for = REQUEST_INTERVAL_SECONDS - (time.monotonic() - _LAST_REQUEST_AT)
        if wait_for > 0:
            time.sleep(wait_for)
        try:
            with urlopen(request, timeout=60) as response:
                _LAST_REQUEST_AT = time.monotonic()
                return json.load(response)
        except HTTPError as error:
            _LAST_REQUEST_AT = time.monotonic()
            if error.code == 429 or error.code in (500, 502, 503, 504):
                retry_after = error.headers.get("Retry-After")
                try:
                    delay = float(retry_after) if retry_after else 5 * (2 ** attempt)
                except ValueError:
                    try:
                        retry_date = parsedate_to_datetime(retry_after)
                        delay = max(1, retry_date.timestamp() - time.time())
                    except (TypeError, ValueError, OverflowError):
                        delay = 5 * (2 ** attempt)
                delay = min(max(delay, 1), 120)
                print(f"HTTP {error.code}; retry {attempt + 1}/6 after {delay:.0f}s")
                if attempt == 5:
                    raise
                time.sleep(delay)
                continue
            raise
        except (URLError, TimeoutError):
            _LAST_REQUEST_AT = time.monotonic()
            if attempt == 5:
                raise
            time.sleep(min(5 * (2 ** attempt), 60))


def clean(value):
    if not value:
        return ""
    value = re.sub(r"<[^>]+>", " ", str(value))
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def commons_filename(file_uri):
    parsed = urlparse(file_uri)
    marker = "/Special:FilePath/"
    if marker not in parsed.path:
        return ""
    return unquote(parsed.path.split(marker, 1)[1]).replace("_", " ")


def get_commons_metadata(filename):
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "titles": "File:" + filename,
        "prop": "imageinfo|videoinfo",
        "iiprop": "url|size|mime|extmetadata",
        "viprop": "duration|size",
    }
    payload = fetch_json(COMMONS_API, params)
    pages = payload.get("query", {}).get("pages", [])
    if not pages or pages[0].get("missing") is not None:
        return None
    page = pages[0]
    image = (page.get("imageinfo") or [{}])[0]
    video = (page.get("videoinfo") or [{}])[0]
    ext = image.get("extmetadata") or {}
    duration = video.get("duration")
    return {
        "commons_file_title": page.get("title"),
        "file_page_url": image.get("descriptionurl"),
        "direct_file_url": image.get("url"),
        "mime_type": image.get("mime"),
        "file_size_bytes": image.get("size"),
        "duration_seconds": duration,
        "license_short_name": clean((ext.get("LicenseShortName") or {}).get("value")),
        "usage_terms": clean((ext.get("UsageTerms") or {}).get("value")),
        "license_url": clean((ext.get("LicenseUrl") or {}).get("value")),
        "artist": clean((ext.get("Artist") or {}).get("value")),
        "attribution": clean((ext.get("Attribution") or {}).get("value")),
        "description": clean((ext.get("ImageDescription") or {}).get("value")),
    }


def main():
    result = fetch_json(SPARQL_ENDPOINT, {"query": QUERY, "format": "json"})
    bindings = result.get("results", {}).get("bindings", [])
    records = []
    seen = set()
    metadata_failures = []

    for row in bindings:
        film_uri = row.get("film", {}).get("value", "")
        video_uri = row.get("video", {}).get("value", "")
        filename = commons_filename(video_uri)
        if not filename or not filename.lower().endswith(VIDEO_EXTENSIONS):
            continue
        if filename.casefold() in seen:
            continue
        seen.add(filename.casefold())

        try:
            metadata = get_commons_metadata(filename)
        except (HTTPError, URLError, TimeoutError) as error:
            code = getattr(error, "code", "network")
            print(f"Skipping metadata temporarily unavailable for {filename}: {code}")
            metadata_failures.append({"filename": filename, "error": str(code)})
            continue
        if not metadata or not metadata.get("direct_file_url"):
            continue

        duration = metadata.get("duration_seconds")
        if not isinstance(duration, (int, float)) or duration < MIN_DURATION_SECONDS:
            continue

        records.append({
            "title": clean(row.get("filmLabel", {}).get("value")) or filename,
            "release_year": row.get("year", {}).get("value"),
            "country": "India",
            "language": None,
            "wikidata_url": film_uri,
            **metadata,
            "source": "Wikidata P10 + Wikimedia Commons file metadata",
            "rights_review_status": "pending_manual_review",
            "commercial_use_allowed": False,
            "playback_status": "not_tested",
        })

    output = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "catalog_scope": "Indian films released before 1964 with a Commons video file longer than 60 minutes",
        "candidate_count": len(records),
        "metadata_failure_count": len(metadata_failures),
        "metadata_failures": metadata_failures,
        "rights_policy": "No item is approved for commercial playback by this index. Verify the individual file license and public-domain status in every relevant territory before enabling playback.",
        "items": records,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(records)} review candidates to {OUTPUT}")


if __name__ == "__main__":
    main()
