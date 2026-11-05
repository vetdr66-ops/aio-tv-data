#!/usr/bin/env python3
"""Build a review-first VOD candidate index from Wikidata + Wikimedia Commons.

This script DOES NOT certify commercial rights. Every item remains blocked until
its Commons license and territorial public-domain status are reviewed manually.
"""
import html
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "public" / "vod" / "index.json"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
START_CATEGORIES = ["Category:Videos of films in the public domain"]
USER_AGENT = "AIO-TV-VOD-Catalog/0.1 (metadata indexing; rights review required)"
MIN_DURATION_SECONDS = 60 * 60
VIDEO_EXTENSIONS = (".webm", ".ogv", ".mp4", ".mkv", ".avi")
REQUEST_INTERVAL_SECONDS = 1.1
_LAST_REQUEST_AT = 0.0


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


def get_category_video_files():
    """Collect video files from the public-domain film category and its subcategories."""
    pending = list(START_CATEGORIES)
    visited_categories = set()
    files = {}

    while pending:
        category = pending.pop(0)
        if category in visited_categories:
            continue
        visited_categories.add(category)
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "list": "categorymembers",
            "cmtitle": category,
            "cmtype": "file|subcat",
            "cmlimit": "500",
        }
        while True:
            payload = fetch_json(COMMONS_API, params)
            members = payload.get("query", {}).get("categorymembers", [])
            for member in members:
                title = member.get("title", "")
                if member.get("ns") == 14 and title.startswith("Category:"):
                    if title not in visited_categories:
                        pending.append(title)
                elif member.get("ns") == 6 and title.lower().endswith(VIDEO_EXTENSIONS):
                    files[title] = category
            continuation = payload.get("continue")
            if not continuation:
                break
            params.update(continuation)

    return files


def get_commons_metadata_batch(file_titles):
    """Fetch metadata for multiple Commons files in one API request."""
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "titles": "|".join(file_titles),
        "prop": "imageinfo|videoinfo",
        "iiprop": "url|size|mime|extmetadata",
        "viprop": "duration|size",
    }
    payload = fetch_json(COMMONS_API, params)
    results = {}

    for page in payload.get("query", {}).get("pages", []):
        if page.get("missing") is not None:
            continue
        image = (page.get("imageinfo") or [{}])[0]
        video = (page.get("videoinfo") or [{}])[0]
        ext = image.get("extmetadata") or {}
        results[page.get("title")] = {
            "commons_file_title": page.get("title"),
            "file_page_url": image.get("descriptionurl"),
            "direct_file_url": image.get("url"),
            "mime_type": image.get("mime"),
            "file_size_bytes": image.get("size"),
            "duration_seconds": video.get("duration"),
            "license_short_name": clean((ext.get("LicenseShortName") or {}).get("value")),
            "usage_terms": clean((ext.get("UsageTerms") or {}).get("value")),
            "license_url": clean((ext.get("LicenseUrl") or {}).get("value")),
            "artist": clean((ext.get("Artist") or {}).get("value")),
            "attribution": clean((ext.get("Attribution") or {}).get("value")),
            "description": clean((ext.get("ImageDescription") or {}).get("value")),
        }

    return results



# Internet Archive's feature_films collection is a second discovery source.
IA_SCRAPE_URL = "https://archive.org/services/search/v1/scrape"
IA_METADATA_URL = "https://archive.org/metadata/{}"
IA_MAX_ITEMS = 3000
IA_REGIONAL_QUERY_LIMIT = 200
IA_REGIONAL_QUERIES = [
    ("hindi", "mediatype:movies AND (language:Hindi OR language:hin)"),
    ("bengali", "mediatype:movies AND (language:Bengali OR language:ben)"),
    ("tamil_telugu", "mediatype:movies AND (language:Tamil OR language:tam OR language:Telugu OR language:tel)"),
    ("arabic_urdu", "mediatype:movies AND (language:Arabic OR language:ara OR language:Urdu OR language:urd)"),
    ("korean", "mediatype:movies AND (language:Korean OR language:kor)"),
    ("chinese", "mediatype:movies AND (language:Chinese OR language:chi OR language:zho)"),
    ("documentaries", "mediatype:movies AND subject:documentary"),
]
IA_WORKERS = 8
IA_ALLOWED_LICENSE = re.compile(
    r"(publicdomain|creativecommons\.org/publicdomain/|creativecommons\.org/licenses/(by|by-sa|by-nd|zero)/)",
    re.I,
)


def ia_json(url, attempts=5):
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    for attempt in range(attempts):
        try:
            with urlopen(request, timeout=60) as response:
                return json.load(response)
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == attempts - 1:
                raise
            retry_after = error.headers.get("Retry-After")
            try:
                delay = min(max(float(retry_after), 2), 90) if retry_after else min(3 * (2 ** attempt), 60)
            except ValueError:
                delay = min(3 * (2 ** attempt), 60)
            time.sleep(delay)
        except (URLError, TimeoutError):
            if attempt == attempts - 1:
                raise
            time.sleep(min(3 * (2 ** attempt), 60))


def ia_scrape_query(query, limit):
    """Fetch at most limit identifiers for one Internet Archive discovery query."""
    params = {
        "q": query,
        "fields": "identifier,title,downloads",
        "count": "500",
    }
    items = []
    cursor = None
    while len(items) < limit:
        request_params = dict(params)
        request_params["count"] = str(min(500, limit - len(items)))
        if cursor:
            request_params["cursor"] = cursor
        payload = ia_json(IA_SCRAPE_URL + "?" + urlencode(request_params))
        batch = payload.get("items", [])
        if not batch:
            break
        items.extend(batch)
        cursor = payload.get("cursor")
        if not cursor:
            break
    return items[:limit]


def ia_list_items():
    """Keep the original feature_films source and add bounded regional/documentary searches."""
    discovery = [
        ("feature_films", "collection:feature_films AND mediatype:movies", IA_MAX_ITEMS)
    ]
    discovery.extend(
        (name, query, IA_REGIONAL_QUERY_LIMIT)
        for name, query in IA_REGIONAL_QUERIES
    )

    unique = {}
    query_stats = []
    total_matches_seen = 0
    for name, query, limit in discovery:
        try:
            found = ia_scrape_query(query, limit)
            total_matches_seen += len(found)
            added = 0
            for item in found:
                identifier = item.get("identifier")
                if identifier and identifier not in unique:
                    item = dict(item)
                    item["_discovery_query"] = query
                    item["_discovery_group"] = name
                    unique[identifier] = item
                    added += 1
            query_stats.append({
                "query_group": name,
                "query": query,
                "limit": limit,
                "records_returned": len(found),
                "new_unique_records": added,
            })
            print(
                f"Internet Archive {name}: returned={len(found)}; "
                f"new_unique={added}; unique_total={len(unique)}"
            )
        except Exception as error:
            query_stats.append({
                "query_group": name,
                "query": query,
                "limit": limit,
                "records_returned": 0,
                "new_unique_records": 0,
                "error": f"{type(error).__name__}: {error}",
            })
            print(f"Internet Archive query {name} unavailable: {error}")

    items = list(unique.values())
    items.sort(
        key=lambda item: (
            item.get("_discovery_group") != "feature_films",
            -int(item.get("downloads") or 0),
        )
    )
    print(
        f"Internet Archive discovery complete: {len(items)} unique identifiers "
        f"from {total_matches_seen} query results"
    )
    return items, total_matches_seen, len(items), query_stats

def ia_duration(value):
    if value in (None, ""):
        return None
    try:
        if ":" in str(value):
            total = 0.0
            for part in str(value).split(":"):
                total = total * 60 + float(part)
            return total
        return float(value)
    except (TypeError, ValueError):
        return None


def ia_fetch_candidate(item):
    identifier = item.get("identifier")
    if not identifier:
        return None, None
    try:
        payload = ia_json(IA_METADATA_URL.format(identifier))
        meta = payload.get("metadata") or {}
        license_url = str(meta.get("licenseurl") or "")
        # Exclude missing, non-commercial, and non-redistributable license labels.
        if not IA_ALLOWED_LICENSE.search(license_url) or re.search(r"(^|[-/])nc([-/]|$)", license_url, re.I):
            return None, None

        files = payload.get("files") or []
        preferred = {"h.264": 0, "h.264 hd": 1, "mpeg4": 2, "512kb mpeg4": 3}
        playable = []
        for file_info in files:
            name = file_info.get("name", "")
            if not name.lower().endswith(".mp4"):
                continue
            fmt = str(file_info.get("format") or "").lower()
            if fmt not in preferred:
                continue
            duration = ia_duration(file_info.get("length"))
            if duration is not None and duration >= MIN_DURATION_SECONDS:
                playable.append((preferred[fmt], name, file_info, duration))
        if not playable:
            return None, None

        playable.sort(key=lambda row: (row[0], row[1]))
        _, filename, video, duration = playable[0]
        runtime = ia_duration((meta.get("runtime") or [None])[0] if isinstance(meta.get("runtime"), list) else meta.get("runtime"))
        if runtime is not None and runtime >= MIN_DURATION_SECONDS:
            duration = runtime
        title = clean((meta.get("title") or [item.get("title") or identifier])[0] if isinstance(meta.get("title"), list) else meta.get("title") or item.get("title") or identifier)
        year_match = re.search(r"\b(18|19|20)\d{2}\b", str(meta.get("year") or meta.get("date") or ""))
        year = int(year_match.group(0)) if year_match else None
        size = video.get("size")
        record = {
            "title": title,
            "release_year": year,
            "country": None,
            "language": None,
            "commons_file_title": None,
            "file_page_url": f"https://archive.org/details/{identifier}",
            "direct_file_url": f"https://archive.org/download/{identifier}/{quote(filename)}",
            "mime_type": "video/mp4",
            "file_size_bytes": int(size) if str(size or "").isdigit() else None,
            "duration_seconds": duration,
            "license_short_name": license_url.rsplit("/", 2)[-2] if license_url.endswith("/") else license_url,
            "usage_terms": "Explicit Internet Archive license URL; verify the underlying work and this file version",
            "license_url": license_url,
            "artist": clean((meta.get("creator") or [""])[0] if isinstance(meta.get("creator"), list) else meta.get("creator")),
            "attribution": "",
            "description": clean((meta.get("description") or [""])[0] if isinstance(meta.get("description"), list) else meta.get("description")),
            "source": f"Internet Archive {item.get('_discovery_group', 'search')} search",
            "source_category": item.get("_discovery_query"),
            "discovery_group": item.get("_discovery_group"),
            "discovery_query": item.get("_discovery_query"),
            "source_identifier": identifier,
            "rights_review_status": "pending_manual_review",
            "commercial_use_allowed": False,
            "playback_status": "not_tested",
        }
        return record, None
    except Exception as error:
        return None, f"{identifier}: {type(error).__name__}: {error}"


def get_internet_archive_candidates():
    items, total_count, unique_count, query_stats = ia_list_items()
    records = []
    failures = []
    with ThreadPoolExecutor(max_workers=IA_WORKERS) as pool:
        futures = [pool.submit(ia_fetch_candidate, item) for item in items]
        for number, future in enumerate(as_completed(futures), 1):
            record, failure = future.result()
            if record:
                records.append(record)
            if failure:
                failures.append(failure)
            if number % 100 == 0 or number == len(futures):
                print(f"Internet Archive metadata processed: {number}/{len(futures)}; candidates={len(records)}")
    return records, total_count, len(items), failures, query_stats, unique_count

def main():
    source_files = get_category_video_files()
    print(f"Commons category scan found {len(source_files)} video files")

    records = []
    metadata_failures = []

    file_items = list(source_files.items())
    batch_size = 20

    for offset in range(0, len(file_items), batch_size):
        batch = file_items[offset:offset + batch_size]
        titles = [title for title, _ in batch]
        try:
            metadata_by_title = get_commons_metadata_batch(titles)
        except (HTTPError, URLError, TimeoutError) as error:
            code = getattr(error, "code", "network")
            print(f"Skipping metadata batch {offset // batch_size + 1}: {code}")
            metadata_failures.extend(
                {"file_title": title, "error": str(code)} for title in titles
            )
            continue

        for file_title, source_category in batch:
            filename = file_title.removeprefix("File:")
            metadata = metadata_by_title.get(file_title)
            if not metadata or not metadata.get("direct_file_url"):
                continue

            duration = metadata.get("duration_seconds")
            if not isinstance(duration, (int, float)) or duration < MIN_DURATION_SECONDS:
                continue

            records.append({
                "title": filename.rsplit(".", 1)[0],
                "release_year": None,
                "country": None,
                "language": None,
                **metadata,
                "source": "Wikimedia Commons public-domain film video category",
                "source_category": source_category,
                "rights_review_status": "pending_manual_review",
                "commercial_use_allowed": False,
                "playback_status": "not_tested",
            })

        print(f"Metadata batches processed: {min(offset + batch_size, len(file_items))}/{len(file_items)}")


    ia_records, ia_total_count, ia_processed_count, ia_failures = [], 0, 0, []
    ia_query_stats, ia_unique_identifier_count = [], 0
    try:
        (
            ia_records,
            ia_total_count,
            ia_processed_count,
            ia_failures,
            ia_query_stats,
            ia_unique_identifier_count,
        ) = get_internet_archive_candidates()
    except Exception as error:
        ia_failures.append(f"discovery scan: {type(error).__name__}: {error}")
        print(f"Internet Archive scan unavailable; keeping Commons results: {error}")
    existing_urls = {record.get("direct_file_url") for record in records}
    for record in ia_records:
        if record.get("direct_file_url") not in existing_urls:
            records.append(record)
            existing_urls.add(record.get("direct_file_url"))
    print(f"Internet Archive candidates added: {len(ia_records)}; metadata failures: {len(ia_failures)}")

    output = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "catalog_scope": "Long-form video candidates discovered through Wikimedia Commons public-domain film categories and bounded Internet Archive feature-film, regional-language, and documentary searches; license metadata is an unverified discovery signal only",
        "source_categories": START_CATEGORIES,
        "scanned_video_file_count": len(source_files),
        "internet_archive_query_result_count": ia_total_count,
        "internet_archive_unique_identifier_count": ia_unique_identifier_count,
        "internet_archive_discovery_queries": ia_query_stats,
        "internet_archive_metadata_processed_count": ia_processed_count,
        "internet_archive_candidate_count": len(ia_records),
        "internet_archive_metadata_failures": ia_failures,
        "candidate_count": len(records),
        "metadata_failure_count": len(metadata_failures),
        "metadata_failures": metadata_failures,
        "rights_policy": "This is a research index only, not a rights-cleared catalog. Wikimedia Commons category membership and Internet Archive licenseurl/rights metadata are discovery clues, not proof of ownership or permission; Internet Archive states it cannot guarantee item copyright status and that license information may be supplied by uploaders. Verify the underlying work, uploader authority, exact file/version, license conditions (including attribution and share-alike), and public-domain status in every target territory before any redistribution or ad-supported playback. No item is approved for commercial use; all items remain pending_manual_review and commercial_use_allowed=false.",
        "items": records,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(records)} review candidates to {OUTPUT}")

if __name__ == "__main__":
    main()
