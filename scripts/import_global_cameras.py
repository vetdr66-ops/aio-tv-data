#!/usr/bin/env python3
"""Import the reviewed Live Environment Streams public camera catalogue."""
import json
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "cameras"
BASE = "https://raw.githubusercontent.com/william-ricchiuti/Live-Environment-Streams/v4.0.0/data"
COUNTRIES = {
    "US": {"name_ar": "الولايات المتحدة", "count": 5948},
    "ID": {"name_ar": "إندونيسيا", "count": 623},
    "TH": {"name_ar": "تايلاند", "count": 155},
    "NO": {"name_ar": "النرويج", "count": 106},
    "TW": {"name_ar": "تايوان", "count": 63},
    "DE": {"name_ar": "ألمانيا", "count": 8},
}
ATTRIBUTION = "Live Environment Streams (William Ricchiuti); retain each camera operator attribution field."
SOURCE_LICENSE = "CC-BY-4.0"


def fetch_country(code):
    url = f"{BASE}/{code}.json"
    request = urllib.request.Request(url, headers={"User-Agent": "AIO-TV-Camera-Catalog/1.0"})
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("type") != "FeatureCollection" or not isinstance(payload.get("features"), list):
        raise ValueError(f"Invalid GeoJSON for {code}")
    return payload["features"], url


def main():
    all_cameras = []
    by_country = defaultdict(list)
    seen_urls = set()
    counts = Counter()

    for code, info in COUNTRIES.items():
        features, source_url = fetch_country(code)
        for feature in features:
            props = feature.get("properties") or {}
            url = props.get("url")
            url_type = props.get("url_type")
            if props.get("status") != "active" or url_type not in {"hls", "mjpeg", "mp4"} or not url:
                continue
            if url in seen_urls:
                continue
            seen_urls.add(url)
            coords = (feature.get("geometry") or {}).get("coordinates") or []
            camera = {
                "id": f"les-{code.lower()}-{len(by_country[code]) + 1}",
                "name": props.get("name") or props.get("display_name") or f"Camera {code}",
                "location": props.get("display_name") or "",
                "country": code,
                "country_name_ar": info["name_ar"],
                "latitude": coords[1] if len(coords) > 1 else None,
                "longitude": coords[0] if len(coords) > 1 else None,
                "stream_url": url,
                "stream_type": url_type,
                "resolution": props.get("resolution"),
                "scene_type": props.get("scene_type"),
                "source_family": props.get("source_family"),
                "last_verified": props.get("last_verified"),
                "operator_attribution": props.get("attribution"),
                "catalog_attribution": ATTRIBUTION,
                "catalog_license": SOURCE_LICENSE,
                "source_catalog": "Live Environment Streams v4.0.0",
                "source_catalog_url": "https://github.com/william-ricchiuti/Live-Environment-Streams",
                "status": "active_in_source_catalog",
            }
            by_country[code].append(camera)
            all_cameras.append(camera)
            counts[code] += 1

        if not by_country[code]:
            raise ValueError(f"No active cameras imported for {code}; refusing empty country: {source_url}")

    OUT.mkdir(parents=True, exist_ok=True)
    for code, cameras in by_country.items():
        path = OUT / "countries" / f"{code.lower()}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "country": code,
            "country_name_ar": COUNTRIES[code]["name_ar"],
            "camera_count": len(cameras),
            "source_catalog": "Live Environment Streams v4.0.0",
            "cameras": cameras,
        }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    index = {
        "section_id": "live_cameras",
        "section_name_ar": "كاميرات حية",
        "grouping": "country",
        "source_catalog": "Live Environment Streams v4.0.0",
        "source_catalog_url": "https://github.com/william-ricchiuti/Live-Environment-Streams",
        "source_catalog_license": SOURCE_LICENSE,
        "total_cameras": len(all_cameras),
        "country_count": len(by_country),
        "country_counts": dict(counts),
        "countries": sorted(by_country),
        "data_path": "cameras/countries/{country}.json",
        "cameras": all_cameras,
    }
    (OUT / "global-index.json").write_text(
        json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print(f"Imported {len(all_cameras)} active camera records across {len(by_country)} countries: {dict(counts)}")


if __name__ == "__main__":
    main()
