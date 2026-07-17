"""Fetch total Google Scholar citations through SerpAPI.

The script is designed to run from any working directory. Generated files are
always written to <repository>/results/ so that the GitHub workflow and the
homepage badge use exactly the same paths.
"""

from __future__ import annotations

import copy
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SERP_API_URL = "https://serpapi.com/search.json"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPOSITORY_ROOT / "results"
SITE_CONFIG = REPOSITORY_ROOT / "_config.yml"

CONNECT_TIMEOUT_SECONDS = 10
READ_TIMEOUT_SECONDS = 45


def scholar_id_from_value(value: str) -> str:
    """Return a Scholar author ID from an ID or a full profile URL."""
    value = value.strip().strip('"\'')
    if not value:
        return ""

    if "://" in value or "citations?" in value:
        parsed = urlparse(value)
        value = parse_qs(parsed.query).get("user", [""])[0].strip()

    if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValueError(
            "Invalid Google Scholar ID. Use the value after 'user=' in the "
            "Google Scholar profile URL."
        )

    return value


def scholar_id_from_site_config(config_path: Path = SITE_CONFIG) -> str:
    """Extract site.author.googlescholar's user parameter from _config.yml."""
    if not config_path.is_file():
        return ""

    text = config_path.read_text(encoding="utf-8")
    match = re.search(
        r"googlescholar\s*:\s*[\"']?"
        r"https?://(?:scholar\.)?google\.[^\s\"']+/citations\?"
        r"[^\s\"']*\buser=([A-Za-z0-9_-]+)",
        text,
        flags=re.IGNORECASE,
    )
    return match.group(1) if match else ""


def get_google_scholar_id() -> str:
    """Resolve the Scholar ID from the environment, then from _config.yml."""
    configured = (
        os.getenv("GOOGLE_SCHOLAR_ID", "").strip()
        or os.getenv("GOOGLE_SCHOLAR_URL", "").strip()
    )
    if configured:
        return scholar_id_from_value(configured)

    scholar_id = scholar_id_from_site_config()
    if scholar_id:
        return scholar_id

    raise RuntimeError(
        "Google Scholar ID is missing. Set GOOGLE_SCHOLAR_ID or configure "
        "author.googlescholar in _config.yml."
    )


def get_serp_api_key() -> str:
    """Read the SerpAPI key without keeping any key in source control."""
    api_key = os.getenv("SERP_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "SERP_API_KEY is missing. Add a repository secret named "
            "SERP_API_KEY under Settings > Secrets and variables > Actions."
        )
    return api_key


def build_http_session() -> requests.Session:
    """Create a session with one bounded retry for transient server failures."""
    retry = Retry(
        total=1,
        connect=1,
        read=0,
        status=1,
        backoff_factor=1,
        status_forcelist=(502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    return session


def fetch_author_data(api_key: str, scholar_id: str) -> dict[str, Any]:
    """Fetch and validate a Google Scholar Author response from SerpAPI."""
    params = {
        "api_key": api_key,
        "engine": "google_scholar_author",
        "author_id": scholar_id,
        "hl": "en",
    }

    print(
        f"Requesting SerpAPI data for Google Scholar ID {scholar_id}...",
        flush=True,
    )

    try:
        with build_http_session() as session:
            response = session.get(
                SERP_API_URL,
                params=params,
                timeout=(CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS),
            )
            response.raise_for_status()
    except requests.Timeout as exc:
        raise RuntimeError(
            "SerpAPI request timed out. The workflow will stop instead of "
            "remaining in 'Get citation data' indefinitely."
        ) from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"SerpAPI HTTP request failed: {exc}") from exc

    try:
        data = response.json()
    except requests.JSONDecodeError as exc:
        preview = response.text[:300].replace("\n", " ")
        raise RuntimeError(
            f"SerpAPI returned non-JSON content: {preview!r}"
        ) from exc

    if not isinstance(data, dict):
        raise RuntimeError("SerpAPI returned an unexpected JSON value.")

    if data.get("error"):
        raise RuntimeError(f"SerpAPI error: {data['error']}")

    status = data.get("search_metadata", {}).get("status")
    if status and status != "Success":
        raise RuntimeError(f"SerpAPI search status is {status!r}, not 'Success'.")

    returned_id = data.get("search_parameters", {}).get("author_id")
    if returned_id and returned_id != scholar_id:
        raise RuntimeError(
            f"SerpAPI returned author_id {returned_id!r}, but {scholar_id!r} "
            "was requested."
        )

    if not isinstance(data.get("author"), dict):
        raise RuntimeError(
            "SerpAPI response does not contain an author object. Confirm that "
            "the Google Scholar profile is public and the author ID is correct."
        )

    return data


def extract_total_citations(data: dict[str, Any]) -> int:
    """Extract total citations from current and legacy SerpAPI schemas."""
    cited_by = data.get("cited_by")
    if not isinstance(cited_by, dict):
        raise RuntimeError("SerpAPI response has no valid 'cited_by' object.")

    # Current Google Scholar Author schema:
    # cited_by.table[*].citations.all
    table = cited_by.get("table")
    if isinstance(table, list):
        for row in table:
            if not isinstance(row, dict):
                continue
            citations = row.get("citations")
            if isinstance(citations, dict) and citations.get("all") is not None:
                return _citation_value_to_int(citations["all"])

    # Compatibility with older forks that stored cited_by.value directly.
    if cited_by.get("value") is not None:
        return _citation_value_to_int(cited_by["value"])

    raise RuntimeError(
        "Could not find total citations at cited_by.table[*].citations.all."
    )


def _citation_value_to_int(value: Any) -> int:
    """Convert integer or formatted string citation values safely."""
    try:
        citations = int(str(value).replace(",", "").strip())
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"Invalid citation value returned by SerpAPI: {value!r}") from exc

    if citations < 0:
        raise RuntimeError(f"Citation count cannot be negative: {citations}")
    return citations


def stable_response_for_storage(data: dict[str, Any]) -> dict[str, Any]:
    """Remove per-request metadata so unchanged citations do not create commits."""
    stored = copy.deepcopy(data)
    metadata = stored.get("search_metadata")
    if isinstance(metadata, dict):
        for key in (
            "id",
            "created_at",
            "processed_at",
            "total_time_taken",
            "json_endpoint",
            "raw_html_file",
        ):
            metadata.pop(key, None)
    return stored


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON atomically to avoid leaving a partial badge file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)
        file.write("\n")
    temporary_path.replace(path)


def main() -> None:
    scholar_id = get_google_scholar_id()
    api_key = get_serp_api_key()
    data = fetch_author_data(api_key=api_key, scholar_id=scholar_id)
    citations = extract_total_citations(data)

    shield_data = {
        "schemaVersion": 1,
        "label": "citations",
        "message": str(citations),
        "color": "9cf",
    }

    write_json_atomic(RESULTS_DIR / "gs_data.json", stable_response_for_storage(data))
    write_json_atomic(RESULTS_DIR / "gs_data_shieldsio.json", shield_data)

    author_name = data.get("author", {}).get("name", "unknown author")
    print(
        f"Citation update complete: {author_name} ({scholar_id}) has "
        f"{citations} citations.",
        flush=True,
    )
    print(f"Wrote citation files to {RESULTS_DIR}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # Keep GitHub Actions logs concise and visible.
        message = str(error).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(
            f"::error title=Google Scholar citation update failed::{message}",
            file=sys.stderr,
            flush=True,
        )
        raise SystemExit(1) from error
