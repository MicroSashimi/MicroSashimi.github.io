import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests

SERP_API_URL = "https://serpapi.com/search"
RESULTS_DIR = Path("results")

# Keep this fallback for compatibility with workflows that replace the literal
# "your API KEY" at runtime. Prefer setting the SERP_API_KEY environment variable.
SERP_API_KEY = os.getenv("SERP_API_KEY", "your API KEY").strip()


def scholar_id_from_value(value: str) -> str:
    """Accept either a Scholar author ID or a full Google Scholar profile URL."""
    value = value.strip().strip('"\'')
    if not value:
        return ""

    if "://" in value or "citations?" in value:
        parsed = urlparse(value)
        value = parse_qs(parsed.query).get("user", [""])[0].strip()

    if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValueError(
            "Invalid Google Scholar author ID. Expected the value after "
            "'user=' in your Scholar profile URL."
        )

    return value


def find_scholar_id_in_site_config() -> str:
    """Find a Google Scholar profile URL in a nearby Jekyll _config.yml file."""
    candidates: list[Path] = []

    # The Action may run from the repository root or from google_scholar_crawler/.
    search_roots = [Path.cwd(), Path(__file__).resolve().parent]
    for root in search_roots:
        for directory in [root, *root.parents]:
            for filename in ("_config.yml", "_config.yaml"):
                candidate = directory / filename
                if candidate not in candidates:
                    candidates.append(candidate)

    pattern = re.compile(
        r"https?://(?:scholar\.)?google\.[^\s\"']+/citations\?[^\s\"']*\buser=([A-Za-z0-9_-]+)",
        re.IGNORECASE,
    )

    for config_path in candidates:
        if not config_path.is_file():
            continue
        text = config_path.read_text(encoding="utf-8")
        match = pattern.search(text)
        if match:
            return match.group(1)

    return ""


def get_google_scholar_id() -> str:
    """Resolve the user's Scholar ID without retaining the fork author's ID."""
    configured_value = (
        os.getenv("GOOGLE_SCHOLAR_ID", "").strip()
        or os.getenv("GOOGLE_SCHOLAR_URL", "").strip()
    )

    if configured_value:
        return scholar_id_from_value(configured_value)

    scholar_id = find_scholar_id_in_site_config()
    if scholar_id:
        return scholar_id

    raise RuntimeError(
        "Google Scholar author ID is not configured. Set GOOGLE_SCHOLAR_ID to "
        "the value after 'user=' in your Scholar profile URL, or put your "
        "Google Scholar profile URL in the site's _config.yml."
    )


def extract_total_citations(data: dict[str, Any]) -> int:
    """Support both older and current SerpAPI Google Scholar response schemas."""
    cited_by = data.get("cited_by", {})
    if not isinstance(cited_by, dict):
        raise ValueError("SerpAPI response has no valid 'cited_by' object.")

    # Older response shape used by some forks.
    legacy_value = cited_by.get("value")
    if legacy_value is not None:
        return int(legacy_value)

    # Current response shape: cited_by.table[*].citations.all
    table = cited_by.get("table", [])
    if isinstance(table, list):
        for row in table:
            if not isinstance(row, dict):
                continue
            citation_stats = row.get("citations")
            if isinstance(citation_stats, dict) and citation_stats.get("all") is not None:
                return int(citation_stats["all"])

    raise ValueError(
        "Could not find total citations in the SerpAPI response. "
        "Inspect results/gs_data.json for the returned schema or API error."
    )


def main() -> None:
    if not SERP_API_KEY or SERP_API_KEY == "your API KEY":
        raise RuntimeError(
            "SERP_API_KEY is not configured. Add it as a GitHub Actions secret "
            "or set the SERP_API_KEY environment variable."
        )

    google_scholar_id = get_google_scholar_id()
    params = {
        "api_key": SERP_API_KEY,
        "engine": "google_scholar_author",
        "author_id": google_scholar_id,
        "hl": "en",
    }

    response = requests.get(SERP_API_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with (RESULTS_DIR / "gs_data.json").open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    if data.get("error"):
        raise RuntimeError(f"SerpAPI error: {data['error']}")

    search_status = data.get("search_metadata", {}).get("status")
    if search_status == "Error":
        raise RuntimeError("SerpAPI search failed; inspect results/gs_data.json.")

    citations = extract_total_citations(data)
    shield_data = {
        "schemaVersion": 1,
        "label": "citations",
        "message": str(citations),
    }
    with (RESULTS_DIR / "gs_data_shieldsio.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(shield_data, f, indent=2, ensure_ascii=False)

    author_name = data.get("author", {}).get("name", "unknown author")
    print(
        f"✅ SerpAPI Done: {author_name} "
        f"(Scholar ID: {google_scholar_id}), citations: {citations}"
    )


if __name__ == "__main__":
    main()
