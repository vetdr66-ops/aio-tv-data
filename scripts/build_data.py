import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "sources"
OUT = ROOT / "public"
DATA = OUT / "data"

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

    streams_by_channel = defaultdict(list)
    unmatched_streams = []
    channel_ids = {channel.get("id") for channel in channels if channel.get("id")}

    # Match names only when the normalized name points to exactly one channel.
    def normalize_name(value):
        return " ".join(str(value or "").strip().casefold().split())

    channel_names = defaultdict(set)
    for channel in channels:
        channel_id = channel.get("id")
        if not channel_id:
            continue
        for name in [channel.get("name"), *(channel.get("alt_names") or [])]:
            normalized = normalize_name(name)
            if normalized:
                channel_names[normalized].add(channel_id)

    matched_by_id = 0
    matched_by_title = 0

    for position, stream in enumerate(streams):
        channel_id = stream.get("channel")
        stream_item = dict(stream)
        stream_item["source_index"] = position

        if channel_id and channel_id in channel_ids:
            streams_by_channel[channel_id].append(stream_item)
            matched_by_id += 1
        elif not channel_id:
            candidates = channel_names.get(normalize_name(stream.get("title")), set())
            if len(candidates) == 1:
                matched_channel_id = next(iter(candidates))
                streams_by_channel[matched_channel_id].append(stream_item)
                stream_item["matched_by"] = "exact_title"
                matched_by_title += 1
            else:
                stream_item["unmatched_reason"] = (
                    "ambiguous_title" if len(candidates) > 1 else "no_exact_title_match"
                )
                unmatched_streams.append(stream_item)
        else:
            stream_item["unmatched_reason"] = "unknown_channel_id"
            stream_item["unmatched_channel_id"] = channel_id
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
        item["streams"] = list(streams_by_channel.get(channel_id, [])) if channel_id else []
        item["stream_count"] = len(item["streams"])
        item["is_nsfw"] = bool(channel.get("is_nsfw"))
        item["is_closed"] = bool(channel.get("closed"))
        item["classification_status"] = "source_category" if original_categories else "needs_review"

        if channel_id:
            channels_by_id[channel_id] = item

        country = safe_key(channel.get("country"))
        by_country[country].append(item)
        country_counts[country] += 1

        for category in original_categories:
            key = safe_key(category)
            by_category[key].append(item)
            category_counts[key] += 1

    # Keep all unmatched source streams for review; source files are never modified.
    unmatched_ids = {
        stream.get("channel")
        for stream in unmatched_streams
        if stream.get("channel")
    }
    channels_with_streams = sum(
        1 for channel in channels
        if channel.get("id") and streams_by_channel.get(channel.get("id"))
    )

    for code, items in by_country.items():
        write_json(DATA / "countries" / f"{code}.json", items)

    for category, items in by_category.items():
        write_json(DATA / "categories" / f"{category}.json", items)

    # Separate review list: channels with at least one linked stream.
    # This does not remove channels from the country/category source datasets.
    channels_with_streams_list = [
        item
        for channel in channels
        if (item := channels_by_id.get(channel.get("id")))
        and item["stream_count"] > 0
    ]
    write_json(DATA / "channels_with_streams.json", channels_with_streams_list)

    write_json(DATA / "unmatched_streams.json", unmatched_streams)
    write_json(DATA / "index.json", {
        "source": "sources/links2.txt and sources/links.txt",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_channels": len(channels),
        "channels_with_ids": sum(1 for channel in channels if channel.get("id")),
        "total_streams": len(streams),
        "streams_with_channel_id": sum(1 for stream in streams if stream.get("channel")),
        "matched_streams_by_id": matched_by_id,
        "matched_streams_by_title": matched_by_title,
        "matched_streams_total": matched_by_id + matched_by_title,
        "channels_with_streams": channels_with_streams,
        "channels_without_streams": len(channels) - channels_with_streams,
        "unmatched_streams": len(unmatched_streams),
        "unmatched_channel_ids": len(unmatched_ids),
        "countries": dict(sorted(country_counts.items())),
        "categories": dict(sorted(category_counts.items())),
        "category_labels": CATEGORY_LABELS,
        "paths": {
            "country": "data/countries/{code}.json",
            "category": "data/categories/{id}.json",
            "unmatched_streams": "data/unmatched_streams.json",
            "channels_with_streams": "data/channels_with_streams.json",
        },
        "retention_policy": "All source channel and stream records are retained; status flags do not remove records.",
    })

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(
        f"Built {len(channels)} channels and {len(streams)} streams; "
        f"{len(by_country)} countries, {len(by_category)} source categories, "
        f"{matched_by_id} matched by ID, {matched_by_title} matched by exact title, "
        f"{channels_with_streams} channels with streams, "
        f"{len(unmatched_streams)} unmatched streams."
    )


if __name__ == "__main__":
    main()
