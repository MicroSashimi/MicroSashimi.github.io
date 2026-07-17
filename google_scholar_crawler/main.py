"""Update the homepage citation badge from a public Google Scholar profile.

This version does not use SerpAPI or any API key. It fetches the public profile
page at a low frequency, parses the citation statistics table, and writes the
result files under <repository>/results/.

Google Scholar has no official public author-metrics API and may occasionally
block automated requests from shared GitHub-hosted runners. On any fetch or
parse failure, this script exits before writing files, so the last known-good
citation value remains on the website.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

SCHOLAR_PROFILE_URL = "https://scholar.google.com/citations"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPOSITORY_ROOT / "results"
SITE_CONFIG = REPOSITORY_ROOT / "_config.yml"

CONNECT_TIMEOUT_SECONDS = 10
READ_TIMEOUT_SECONDS = 30
MAX_ATTEMPTS = 2

# Rotate between two ordinary desktop browser identifiers. This does not bypass
# a CAPTCHA; it only avoids being rejected for using requests' default UA.
USER_AGENTS = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
)

BLOCK_MARKERS = (
    "unusual traffic",
    "not a robot",
    "our systems have detected",
    "recaptcha",
    "/sorry/",
)


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
    """Extract author.googlescholar's user parameter from _config.yml."""
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
    """Resolve the Scholar ID from environment variables or _config.yml."""
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


def request_headers(user_agent: str) -> dict[str, str]:
    return {
        "User-Agent": user_agent,
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Upgrade-Insecure-Requests": "1",
    }


def looks_blocked(response: requests.Response) -> bool:
    """Detect common Google bot-check/rate-limit responses."""
    lowered = response.text[:200_000].lower()
    return (
        response.status_code in {403, 429}
        or "/sorry/" in response.url.lower()
        or any(marker in lowered for marker in BLOCK_MARKERS)
    )


def fetch_profile_html(scholar_id: str) -> tuple[str, str]:
    """Fetch a public Scholar profile with bounded attempts and timeouts."""
    params = {"user": scholar_id, "hl": "en", "oi": "ao"}
    errors: list[str] = []

    for attempt in range(1, MAX_ATTEMPTS + 1):
        user_agent = USER_AGENTS[(attempt - 1) % len(USER_AGENTS)]
        print(
            f"Fetching public Google Scholar profile {scholar_id} "
            f"(attempt {attempt}/{MAX_ATTEMPTS})...",
            flush=True,
        )

        try:
            response = requests.get(
                SCHOLAR_PROFILE_URL,
                params=params,
                headers=request_headers(user_agent),
                timeout=(CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS),
                allow_redirects=True,
            )
        except requests.Timeout:
            errors.append(f"attempt {attempt}: request timed out")
        except requests.RequestException as exc:
            errors.append(f"attempt {attempt}: HTTP request failed: {exc}")
        else:
            if looks_blocked(response):
                errors.append(
                    f"attempt {attempt}: Google blocked the shared runner "
                    f"(HTTP {response.status_code}, URL {response.url})"
                )
            elif response.status_code != 200:
                errors.append(
                    f"attempt {attempt}: unexpected HTTP {response.status_code}"
                )
            elif not response.text.strip():
                errors.append(f"attempt {attempt}: empty response body")
            else:
                return response.text, response.url

        if attempt < MAX_ATTEMPTS:
            time.sleep(8)

    details = "; ".join(errors)
    raise RuntimeError(
        "Could not fetch the public Google Scholar profile. The last known "
        "citation JSON was not changed. " + details
    )


def _number(text: str, field_name: str) -> int:
    compact = re.sub(r"[^0-9]", "", text)
    if not compact:
        raise RuntimeError(f"Google Scholar returned no numeric {field_name} value.")
    return int(compact)


def parse_profile_html(html: str, scholar_id: str, response_url: str) -> dict[str, Any]:
    """Parse author name and citation statistics from the profile page."""
    soup = BeautifulSoup(html, "html.parser")

    author_node = soup.select_one("#gsc_prf_in")
    author_name = author_node.get_text(" ", strip=True) if author_node else ""
    if not author_name:
        title = soup.title.get_text(" ", strip=True) if soup.title else "unknown page"
        raise RuntimeError(
            "The response was not a recognizable public Scholar profile "
            f"(page title: {title!r}). Confirm that the profile is public."
        )

    metrics: dict[str, dict[str, int | None]] = {}
    stats_table = soup.select_one("#gsc_rsb_st")
    if stats_table is None:
        raise RuntimeError(
            "The Google Scholar statistics table '#gsc_rsb_st' was not found. "
            "Google may have changed the page layout."
        )

    for row in stats_table.select("tr"):
        label_node = row.select_one("td.gsc_rsb_sc1")
        value_nodes = row.select("td.gsc_rsb_std")
        if label_node is None or not value_nodes:
            continue

        label = " ".join(label_node.get_text(" ", strip=True).lower().split())
        all_value = _number(value_nodes[0].get_text(" ", strip=True), label)
        recent_value = (
            _number(value_nodes[1].get_text(" ", strip=True), f"recent {label}")
            if len(value_nodes) > 1
            else None
        )
        metrics[label] = {"all": all_value, "recent": recent_value}

    citations = metrics.get("citations")
    if citations is None:
        raise RuntimeError(
            "The 'Citations' row was not found in the Google Scholar profile."
        )

    parsed_url_id = parse_qs(urlparse(response_url).query).get("user", [""])[0]
    if parsed_url_id and parsed_url_id != scholar_id:
        raise RuntimeError(
            f"Google returned profile {parsed_url_id!r}, but {scholar_id!r} was requested."
        )

    return {
        "source": "Google Scholar public profile",
        "profile_url": f"{SCHOLAR_PROFILE_URL}?user={scholar_id}&hl=en",
        "author": {"name": author_name, "scholar_id": scholar_id},
        "citations": citations,
        "h_index": metrics.get("h-index"),
        "i10_index": metrics.get("i10-index"),
    }


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON atomically so a failed run cannot leave a partial file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)
        file.write("\n")
    temporary_path.replace(path)


def main() -> None:
    scholar_id = get_google_scholar_id()
    html, response_url = fetch_profile_html(scholar_id)
    data = parse_profile_html(html, scholar_id, response_url)

    citations = int(data["citations"]["all"])
    shield_data = {
        "schemaVersion": 1,
        "label": "citations",
        "message": str(citations),
        "color": "9cf",
    }

    # Only write after fetching and parsing have both succeeded. A blocked or
    # malformed response therefore cannot replace a valid value with zero.
    write_json_atomic(RESULTS_DIR / "gs_data.json", data)
    write_json_atomic(RESULTS_DIR / "gs_data_shieldsio.json", shield_data)

    author_name = data["author"]["name"]
    print(
        f"Citation update complete: {author_name} ({scholar_id}) has "
        f"{citations} citations.",
        flush=True,
    )
    print(f"Wrote citation files to {RESULTS_DIR}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # GitHub Actions workflow-command escaping for a readable error banner.
        message = str(error).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(
            f"::error title=Google Scholar citation update failed::{message}",
            file=sys.stderr,
            flush=True,
        )
        raise SystemExit(1) from error
