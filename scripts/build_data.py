import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "sources"
OUT = ROOT / "public"
DATA = OUT / "data"
OVERRIDES_FILE = ROOT / "admin" / "overrides.json"

# Source categories are preserved exactly. These labels are presentation metadata,
# not guesses about a channel's language, genre, or programming.
CATEGORY_LABELS = {
    "movies": "أفلام",
    "series": "مسلسلات ودراما",
    "comedy": "كوميديا",
    "classic": "كلاسيكيات",
    "sports": "رياضة",
    "news": "أخبار",
    "religious": "ديني",
    "music": "موسيقى",
    "kids": "أطفال",
    "animation": "رسوم متحركة",
    "education": "تعليم",
    "culture": "ثقافة",
    "documentary": "وثائقيات",
    "science": "علوم",
    "travel": "سفر وسياحة",
    "cooking": "طبخ",
    "business": "أعمال واقتصاد",
    "lifestyle": "أسلوب حياة",
    "outdoor": "أنشطة خارجية",
    "auto": "سيارات",
    "weather": "طقس",
    "legislative": "تشريعات وبرلمان",
    "shop": "تسوق",
    "family": "عائلي",
    "public": "قنوات عامة",
    "general": "عام",
    "entertainment": "ترفيه",
    "relax": "استرخاء",
    "interactive": "تفاعلي",
    "xxx": "محتوى للبالغين",
}


def load_source(filename):
    path = SOURCES / filename
    with path.open("r", encoding="utf-8") as source_file:
        value = json.load(source_file)
    if not isinstance(value, list):
        raise ValueError(f"Expected a JSON array in {path}")
    return value


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def safe_key(value):
    return str(value or "unknown").strip().lower() or "unknown"


def main():
    # Read the two user-provided source files; do not discard any source records.
    streams = load_source("links.txt")
    channels = load_source("links2.txt")
    with OVERRIDES_FILE.open("r", encoding="utf-8") as overrides_file:
        admin_data = json.load(overrides_file)
    channel_overrides = admin_data.get("channels", {})
    added_channels = admin_data.get("added_channels", {})
    existing_ids = {channel.get("id") for channel in channels if channel.get("id")}
    for added_id, added_channel in added_channels.items():
        if added_id in existing_ids:
            raise ValueError(f"Admin channel ID already exists in source: {added_id}")
        channels.append({**added_channel, "id": added_id, "is_admin_added": True})

    streams_by_channel = defaultdict(list)
    unmatched_streams = []

    for position, stream in enumerate(streams):
        channel_id = stream.get("channel")
        stream_item = dict(stream)
        stream_item["source_index"] = position
        if channel_id:
            streams_by_channel[channel_id].append(stream_item)
        else:
            unmatched_streams.append(stream_item)

    channels_by_id = {}
    by_country = defaultdict(list)
    by_category = defaultdict(list)
    country_counts = defaultdict(int)
    category_counts = defaultdict(int)

    for position, channel in enumerate(channels):
        channel_id = channel.get("id")
        original_categories = channel.get("categories") or []
        localized_categories = [
            {
                "id": safe_key(category),
                "name": CATEGORY_LABELS.get(safe_key(category), safe_key(category)),
                "source": "iptv-org",
            }
            for category in original_categories
        ]

        item = dict(channel)
        item["source_index"] = position
        item["original_categories"] = original_categories
        item["localized_categories"] = localized_categories
        item["streams"] = list(channel.get("streams", streams_by_channel.get(channel_id, []))) if channel_id else []
        item["stream_count"] = len(item["streams"])
        item["is_nsfw"] = bool(channel.get("is_nsfw"))
        item["is_closed"] = bool(channel.get("closed"))
        item["classification_status"] = "source_category" if original_categories else "needs_review"

        # Apply manager changes to generated output only; source files remain untouched.
        override = channel_overrides.get(channel_id, {}) if channel_id else {}
        item["admin_override"] = override
        if override.get("display_name"):
            item["original_name"] = channel.get("name")
            item["name"] = override["display_name"]
        if "logo" in override:
            item["logo"] = override["logo"]
        if "country" in override:
            item["country"] = safe_key(override["country"])
        if "categories" in override:
            item["categories"] = override["categories"]
            item["localized_categories"] = [
                {
                    "id": safe_key(category),
                    "name": CATEGORY_LABELS.get(safe_key(category), safe_key(category)),
                    "source": "admin",
                }
                for category in override["categories"]
            ]
        if "streams" in override:
            item["streams"] = override["streams"]
            item["stream_count"] = len(item["streams"])
        if "enabled" in override:
            item["is_admin_disabled"] = not bool(override["enabled"])

        if channel_id:
            channels_by_id[channel_id] = item

        if override.get("enabled") is False:
            continue

        country = safe_key(item.get("country"))
        by_country[country].append(item)
        country_counts[country] += 1

        for category in item.get("categories", original_categories):
            key = safe_key(category)
            by_category[key].append(item)
            category_counts[key] += 1

    # Keep every stream, including duplicates, unsupported schemes, missing IDs,
    # and IDs that have no matching channel metadata.
    unmatched_ids = set()
    for position, stream in enumerate(streams):
        channel_id = stream.get("channel")
        if channel_id and channel_id not in channels_by_id:
            unmatched_ids.add(channel_id)
            unmatched_streams.append({
                **stream,
                "source_index": position,
                "unmatched_channel_id": channel_id,
            })

    for code, items in by_country.items():
        write_json(DATA / "countries" / f"{code}.json", items)

    for category, items in by_category.items():
        write_json(DATA / "categories" / f"{category}.json", items)

    write_json(DATA / "unmatched_streams.json", unmatched_streams)
    write_json(DATA / "index.json", {
        "source": "sources/links2.txt and sources/links.txt",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_channels": len(channels),
        "channels_with_ids": sum(1 for channel in channels if channel.get("id")),
        "total_streams": len(streams),
        "streams_with_channel_id": sum(1 for stream in streams if stream.get("channel")),
        "unmatched_streams": len(unmatched_streams),
        "unmatched_channel_ids": len(unmatched_ids),
        "countries": dict(sorted(country_counts.items())),
        "categories": dict(sorted(category_counts.items())),
        "category_labels": CATEGORY_LABELS,
        "paths": {
            "country": "data/countries/{code}.json",
            "category": "data/categories/{id}.json",
            "unmatched_streams": "data/unmatched_streams.json",
        },
        "retention_policy": "All source channel and stream records are retained; status flags do not remove records.",
    })

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(
        f"Built {len(channels)} channels and {len(streams)} streams; "
        f"{len(by_country)} countries, {len(by_category)} source categories, "
        f"{len(unmatched_streams)} unmatched streams."
    )


if __name__ == "__main__":
    main()
