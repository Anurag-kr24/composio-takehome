import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from composio import Composio
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APPS_FILE = PROJECT_ROOT / "data" / "raw" / "apps.json"
RAW_EVIDENCE_FILE = PROJECT_ROOT / "data" / "raw" / "research_evidence.json"

COMPOSIO_SEARCH_VERSION = "20260903_00"


SEARCH_QUERIES = {
    "description": (
        "{app} developer platform API integrations official documentation"
    ),
    "authentication": (
        "{app} developer API authentication OAuth API key access token "
        "official documentation"
    ),
    "credential_access": (
        "{app} developer portal create app get API credentials access token "
        " registration approval sales enterprise official documentation"
    ),
    "api": (
        "{app} developer API documentation endpoints CRM integrations "
        "official documentation"
    ),
    "mcp": (
        "{app} MCP Model Context Protocol official developer documentation"
    ),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_apps() -> list[dict[str, Any]]:
    with APPS_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_composio_client() -> Composio:
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

    api_key = os.getenv("COMPOSIO_API_KEY")
    if not api_key:
        raise RuntimeError("COMPOSIO_API_KEY is not configured")

    return Composio(api_key=api_key)


def execute_search(
    composio: Composio,
    query: str,
) -> dict[str, Any]:
    return composio.tools.execute(
        slug="COMPOSIO_SEARCH_WEB",
        version=COMPOSIO_SEARCH_VERSION,
        arguments={"query": query},
    )


def execute_fetch(
    composio: Composio,
    urls: list[str],
) -> dict[str, Any]:
    return composio.tools.execute(
        slug="COMPOSIO_SEARCH_FETCH_URL_CONTENT",
        version=COMPOSIO_SEARCH_VERSION,
        arguments={
            "urls": urls,
            "text": True,
            "max_characters": 12000,
        },
    )


def extract_citations(search_result: dict[str, Any]) -> list[dict[str, Any]]:
    data = search_result.get("data") or {}
    return data.get("citations") or []


def choose_official_urls(
    app_record: dict[str, Any],
    citations: list[dict[str, Any]],
) -> list[str]:
    """
    Conservative source selection using an explicit official-domain map.

    Search results remain discovery evidence. Only URLs on known official
    domains are promoted to the first-pass fetch set.
    """
    official_domains = [
        domain.lower().strip()
        for domain in app_record.get("official_domains", [])
    ]

    selected: list[str] = []

    for citation in citations:
        url = citation.get("url", "")
        hostname = urlparse(url).hostname

        if not hostname:
            continue

        hostname = hostname.lower().rstrip(".")

        if any(
            hostname == domain or hostname.endswith("." + domain)
            for domain in official_domains
        ):
            if url not in selected:
                selected.append(url)

    return selected[:5]


def research_app(
    composio: Composio,
    app_record: dict[str, Any],
) -> dict[str, Any]:
    app = app_record["app"]

    result: dict[str, Any] = {
        "app": app,
        "domain": app_record.get("domain"),
        "category": app_record.get("category"),
        "research_started_at": utc_now(),
        "searches": [],
        "fetched_sources": [],
    }

    for evidence_area, template in SEARCH_QUERIES.items():
        query = template.format(app=app)

        print(f"[search] {app} | {evidence_area}")

        search_result = execute_search(composio, query)

        citations = extract_citations(search_result)
        candidate_urls = choose_official_urls(app_record, citations)

        result["searches"].append(
            {
                "evidence_area": evidence_area,
                "query": query,
                "successful": search_result.get("successful", False),
                "answer": (search_result.get("data") or {}).get("answer"),
                "citations": citations,
                "candidate_urls": candidate_urls,
                "retrieved_at": utc_now(),
            }
        )

        if candidate_urls:
            print(
                f"[fetch] {app} | {evidence_area} | "
                f"{len(candidate_urls)} candidate source(s)"
            )

            fetch_result = execute_fetch(
                composio,
                candidate_urls,
            )

            result["fetched_sources"].append(
                {
                    "evidence_area": evidence_area,
                    "successful": fetch_result.get("successful", False),
                    "result": fetch_result.get("data"),
                    "retrieved_at": utc_now(),
                }
            )

        # Respect the search tool's documented throttling guidance.
        time.sleep(1.0)

    return result


def save_evidence(records: list[dict[str, Any]]) -> None:
    RAW_EVIDENCE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with RAW_EVIDENCE_FILE.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def main() -> None:
    composio = get_composio_client()
    apps = load_apps()

    print(f"Loaded {len(apps)} app(s)")

    records = []

    for app_record in apps:
        records.append(research_app(composio, app_record))

    save_evidence(records)

    print()
    print(f"Saved evidence to: {RAW_EVIDENCE_FILE}")


if __name__ == "__main__":
    main()
