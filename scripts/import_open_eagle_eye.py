#!/usr/bin/env python3
"""Import verified, unauthenticated public snapshot cameras from Open Eagle Eye."""
import json
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "cameras" / "sources" / "open-eagle-eye"
SOURCE_URL = "https://raw.githubusercontent.com/stuchapin909/Open-Eagle-Eye/master/cameras.json"
LICENSE_URL = "https://github.com/stuchapin909/Open-Eagle-Eye/blob/master/LICENSE"
CATALOG_URL = "https://github.com/stuchapin909/Open-Eagle-Eye"
COUNTRY_NAMES_AR = {
    "US": "الولايات المتحدة", "FI": "فنلندا", "CA": "كندا",
    "HK": "هونغ كونغ", "GB": "المملكة المتحدة", "NZ": "نيوزيلندا",
    "AU": "أستراليا", "BR": "البرازيل", "JP": "اليابان",
    "SG": "سنغافورة", "IE": "أيرلندا",
}


def main():
    request = urllib.request.Request(
        SOURCE_URL, headers={"User-Agent": "AIO-TV-Camera-Catalog/1.0"}
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Open Eagle Eye registry is not a JSON list")

    by_country = defaultdict(list)
    seen = set()
    for item in payload:
        if not isinstance(item, dict) or item.get("verified") is not True:
            continue
        if item.get("auth") is not False:
            continue
        url = item.get("url")
        if not isinstance(url, str) or not url.startswith("https://"):
            continue
        if not url.lower().split("?", 1)[0].endswith((".jpg", ".jpeg", ".png")):
            continue
        if url in seen:
            continue
        country = str(item.get("country") or "").upper()
        camera_id = item.get("id")
        coords = item.get("coordinates") or {}
        if len(country) != 2 or not camera_id:
            continue
        lat, lng = coords.get("lat"), coords.get("lng")
        if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
            continue
        seen.add(url)
        by_country[country].append({
            "id": str(camera_id),
            "name": item.get("name") or str(camera_id),
            "city": item.get("city") or "",
            "location": item.get("location") or "",
            "country": country,
            "country_name_ar": COUNTRY_NAMES_AR.get(country, country),
            "timezone": item.get("timezone"),
            "latitude": lat,
            "longitude": lng,
            "stream_url": url,
            "stream_type": "snapshot",
            "image_format": "jpeg" if ".jpg" in url.lower() or ".jpeg" in url.lower() else "png",
            "category": item.get("category"),
            "operator_auth_required": False,
            "verified_in_source_catalog": True,
            "catalog_attribution": "Open Eagle Eye (stuchapin909)",
            "catalog_license": "MIT",
            "source_catalog": "Open Eagle Eye",
            "source_catalog_url": CATALOG_URL,
            "source_license_url": LICENSE_URL,
            "status": "verified_in_source_catalog",
        })

    if not by_country:
        raise ValueError("No eligible public cameras found; refusing empty output")

    OUT.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    all_cameras = []
    for country, cameras in sorted(by_country.items()):
        counts[country] = len(cameras)
        all_cameras.extend(cameras)
        path = OUT / "countries" / f"{country.lower()}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "country": country,
            "country_name_ar": COUNTRY_NAMES_AR.get(country, country),
            "camera_count": len(cameras),
            "source_catalog": "Open Eagle Eye",
            "source_catalog_url": CATALOG_URL,
            "catalog_license": "MIT",
            "cameras": cameras,
        }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    index = {
        "section_id": "live_cameras",
        "section_name_ar": "كاميرات حية",
        "source_catalog": "Open Eagle Eye",
        "source_catalog_url": CATALOG_URL,
        "source_catalog_license": "MIT",
        "license_notice": "Retain the upstream MIT copyright and license notice.",
        "total_cameras": len(all_cameras),
        "country_count": len(by_country),
        "country_counts": dict(counts),
        "countries": sorted(by_country),
        "data_path": "cameras/sources/open-eagle-eye/countries/{country}.json",
        "camera_type": "public live snapshots (JPEG/PNG), not video streams",
        "cameras": all_cameras,
    }
    (OUT / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print(f"Imported {len(all_cameras)} verified public snapshots across {len(by_country)} countries: {dict(counts)}")


if __name__ == "__main__":
    main()
