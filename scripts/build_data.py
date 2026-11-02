import json
import urllib.request
from collections import defaultdict
from pathlib import Path

BASE = "https://iptv-org.github.io/api"
OUT = Path("public")
DATA = OUT / "data"


def load(name):
    request = urllib.request.Request(
        f"{BASE}/{name}.json",
        headers={"User-Agent": "aio-tv-data-builder/1.0"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.load(response)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def main():
    channels = load("channels")
    streams = load("streams")
    blocklist = load("blocklist")

    blocked = {item.get("channel") for item in blocklist}
    streams_by_channel = defaultdict(list)

    for stream in streams:
        channel_id = stream.get("channel")
        url = stream.get("url", "")
        if channel_id and url.startswith(("http://", "https://")):
            streams_by_channel[channel_id].append({
                "url": url,
                "title": stream.get("title"),
                "quality": stream.get("quality"),
                "referrer": stream.get("referrer"),
                "user_agent": stream.get("user_agent"),
                "labels": stream.get("labels", []),
            })

    by_country = defaultdict(list)
    by_category = defaultdict(list)
    country_counts = defaultdict(int)
    category_counts = defaultdict(int)
    total = 0

    for channel in channels:
        channel_id = channel.get("id")
        if not channel_id or channel_id in blocked or channel.get("is_nsfw"):
            continue

        channel_streams = streams_by_channel.get(channel_id, [])
        if not channel_streams:
            continue

        item = {
            "id": channel_id,
            "name": channel.get("name"),
            "country": channel.get("country"),
            "categories": channel.get("categories") or [],
            "languages": channel.get("languages") or [],
            "logo": channel.get("logo"),
            "website": channel.get("website"),
            "streams": channel_streams,
        }

        country = (channel.get("country") or "unknown").lower()
        by_country[country].append(item)
        country_counts[country] += 1

        for category in item["categories"]:
            key = category.lower()
            by_category[key].append(item)
            category_counts[key] += 1

        total += 1

    for code, items in by_country.items():
        write_json(DATA / "countries" / f"{code}.json", items)

    for category, items in by_category.items():
        write_json(DATA / "categories" / f"{category}.json", items)

    write_json(DATA / "index.json", {
        "source": "https://github.com/iptv-org/api",
        "generated_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "total_channels": total,
        "countries": dict(sorted(country_counts.items())),
        "categories": dict(sorted(category_counts.items())),
        "paths": {
            "country": "data/countries/{code}.json",
            "category": "data/categories/{id}.json",
        },
    })

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(
        f"Built {total} channels, {len(by_country)} countries, "
        f"{len(by_category)} categories."
    )


if __name__ == "__main__":
    main()
