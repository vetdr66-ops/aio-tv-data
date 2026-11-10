#!/usr/bin/env python3
"""Build public radio JSON catalogs from admin/overrides.json."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES_PATH = ROOT / "admin" / "overrides.json"
OUTPUT_DIR = ROOT / "public" / "radio"
CATALOGS = {
    "radio_arabic_quran": "radio_arabic_quran.json",
    "radio_world": "radio_world.json",
}


def main():
    overrides = json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
    catalogs = overrides.get("radio_catalogs")
    if not isinstance(catalogs, dict):
        raise SystemExit("admin/overrides.json is missing radio_catalogs")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for key, filename in CATALOGS.items():
        catalog = catalogs.get(key)
        if not isinstance(catalog, dict) or not isinstance(catalog.get("stations"), list):
            raise SystemExit(f"Invalid radio catalog: {key}")
        ids = [station.get("id") for station in catalog["stations"]]
        if any(not isinstance(value, str) or not value.strip() for value in ids):
            raise SystemExit(f"Every station in {key} must have a non-empty id")
        if len(ids) != len(set(ids)):
            raise SystemExit(f"Duplicate station ids found in {key}")
        for station in catalog["stations"]:
            for field in ("name", "country", "country_code"):
                if not isinstance(station.get(field), str) or not station[field].strip():
                    raise SystemExit(f"Station {station['id']} has invalid {field}")
            stream_url = station.get("stream_url", "")
            if stream_url and not stream_url.startswith(("http://", "https://")):
                raise SystemExit(f"Station {station['id']} has an invalid stream_url")
        target = OUTPUT_DIR / filename
        target.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Built {target.relative_to(ROOT)}: {len(catalog['stations'])} stations")


if __name__ == "__main__":
    main()
