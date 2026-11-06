import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "sources" / "cameras.json"
OUT = ROOT / "public" / "cameras"


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def main():
    catalog = json.loads(SOURCE.read_text(encoding="utf-8"))
    if catalog.get("section_id") != "live_cameras":
        raise ValueError("Invalid camera section id")

    active = catalog.get("sources", [])
    pending = catalog.get("pending_sources", [])
    seen = set()

    for source in active + pending:
        source_id = source.get("id")
        country = source.get("country")
        if not source_id or not country:
            raise ValueError("Every camera source needs id and country")
        if source_id in seen:
            raise ValueError(f"Duplicate camera source id: {source_id}")
        seen.add(source_id)
        if source.get("status") == "active" and not source.get("api_url"):
            raise ValueError(f"Active source has no API URL: {source_id}")

    by_country = defaultdict(list)
    for source in active:
        by_country[source["country"]].append(source)

    index = {
        "schema_version": catalog["schema_version"],
        "section_id": catalog["section_id"],
        "section_name_ar": catalog["section_name_ar"],
        "grouping": catalog["grouping"],
        "active_source_count": len(active),
        "pending_source_count": len(pending),
        "countries": sorted(by_country.keys()),
        "sources": active,
        "pending_sources": pending,
    }
    write_json(OUT / "index.json", index)

    for country, sources in by_country.items():
        write_json(OUT / "countries" / f"{country.lower()}.json", {
            "country": country,
            "sources": sources,
        })

    print(
        f"Built camera source catalog: {len(active)} active sources, "
        f"{len(pending)} pending sources, {len(by_country)} countries."
    )


if __name__ == "__main__":
    main()
