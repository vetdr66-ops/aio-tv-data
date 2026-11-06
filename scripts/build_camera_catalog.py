#!/usr/bin/env python3
"""Build one country-aware index for video streams and live snapshots."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAMERAS = ROOT / "public" / "cameras"


def load(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    video = load(CAMERAS / "global-index.json")
    snapshots = load(CAMERAS / "sources" / "open-eagle-eye" / "index.json")
    api = load(CAMERAS / "index.json")

    video_items = video.get("cameras", [])
    snapshot_items = snapshots.get("cameras", [])
    video_countries = set(video.get("countries", []))
    snapshot_countries = set(snapshots.get("countries", []))
    api_countries = set(api.get("countries", []))
    all_countries = sorted(video_countries | snapshot_countries | api_countries)

    result = {
        "schema_version": 1,
        "section_id": "live_cameras",
        "section_name_ar": "كاميرات حية",
        "grouping": "country",
        "generated_by": "AIO_TV camera data pipeline",
        "camera_types": {
            "video": {
                "description": "Direct HLS/MJPEG/MP4 public streams",
                "count": len(video_items),
                "countries": sorted(video_countries),
                "data_file": "global-index.json",
            },
            "snapshots": {
                "description": "Verified public JPEG/PNG snapshots; refreshed by source operator",
                "count": len(snapshot_items),
                "countries": sorted(snapshot_countries),
                "data_file": "sources/open-eagle-eye/index.json",
            },
        },
        "api_source_catalog": {
            "data_file": "index.json",
            "active_source_count": api.get("active_source_count", 0),
            "pending_source_count": api.get("pending_source_count", 0),
            "countries": sorted(api_countries),
        },
        "country_count": len(all_countries),
        "countries": all_countries,
        "country_coverage": {
            code: {
                "video_streams": video.get("country_counts", {}).get(code, 0),
                "snapshots": snapshots.get("country_counts", {}).get(code, 0),
                "api_sources": sum(1 for s in api.get("sources", []) if s.get("country") == code),
                "pending_api_sources": sum(1 for s in api.get("pending_sources", []) if s.get("country") == code),
            }
            for code in all_countries
        },
        "source_catalogs": [
            {
                "name": "Live Environment Streams v4.0.0",
                "license": video.get("source_catalog_license", "See upstream source review"),
                "url": video.get("source_catalog_url"),
                "camera_type": "video",
            },
            {
                "name": "Open Eagle Eye",
                "license": snapshots.get("source_catalog_license", "MIT"),
                "url": snapshots.get("source_catalog_url"),
                "camera_type": "snapshot",
            },
        ],
    }
    if not video_items and not snapshot_items and not api.get("sources"):
        raise ValueError("No camera sources found; refusing to publish an empty catalog")
    (CAMERAS / "catalog.json").write_text(
        json.dumps(result, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print(
        f"Camera catalog ready: {len(video_items)} video records, "
        f"{len(snapshot_items)} snapshots, {len(all_countries)} countries, "
        f"{len(api.get('sources', []))} API sources ({len(api.get('pending_sources', []))} pending)."
    )


if __name__ == "__main__":
    main()
