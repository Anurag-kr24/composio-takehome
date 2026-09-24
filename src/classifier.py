import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.schema import (
    APIAssessment,
    AccessAssessment,
    AppResearchRecord,
    BuildabilityAssessment,
    Confidence,
    Evidence,
    MCPAssessment,
    Verification,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "research_evidence.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "classified_records.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_research() -> list[dict[str, Any]]:
    with INPUT_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_records(records: list[dict[str, Any]]) -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def iter_sources(record: dict[str, Any]):
    """
    Yield:
        evidence_area, source_url, source_title, source_text
    """
    for fetched in record.get("fetched_sources", []):
        evidence_area = fetched.get("evidence_area", "")
        result = fetched.get("result") or {}
        results = result.get("results") or []

        for item in results:
            text = item.get("text") or ""

            yield (
                evidence_area,
                item.get("url", ""),
                item.get("title") or None,
                text,
            )


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def has_phrase(text: str, *phrases: str) -> bool:
    lower = text.lower()
    return any(phrase.lower() in lower for phrase in phrases)


def add_evidence(
    evidence: list[Evidence],
    *,
    claim: str,
    url: str,
    source_title: str | None,
    evidence_note: str,
) -> None:
    if not url:
        return

    # Deduplicate identical claim/source pairs.
    key = (claim, url)

    for existing in evidence:
        if (existing.claim, existing.url) == key:
            return

    evidence.append(
        Evidence(
            claim=claim,
            url=url,
            source_title=source_title,
            source_type="official_docs",
            evidence_note=evidence_note,
            retrieved_at=utc_now(),
            supports_claim=True,
            verification_status="unverified",
        )
    )


def collect_authentication(
    record: dict[str, Any],
    evidence: list[Evidence],
) -> tuple[list[str], str, str]:
    """
    Detect authentication mechanisms from explicit authentication evidence.

    Important distinction:
    - access token is an authentication credential
    - Bearer is generally a transport/header convention
    Therefore Bearer is not independently reported as a credential type.
    """
    methods: list[str] = []
    source_texts: list[tuple[str, str | None, str]] = []

    for area, url, title, text in iter_sources(record):
        if area != "authentication":
            continue

        if text.strip():
            source_texts.append((url, title, text))

    def add_method(method: str) -> None:
        if method not in methods:
            methods.append(method)

    for url, title, text in source_texts:
        lower = text.lower()

        if re.search(r"\boauth(?:\s*2(?:\.0)?)?\b", lower):
            add_method("OAuth 2.0")
            add_evidence(
                evidence,
                claim="OAuth 2.0 authentication is documented.",
                url=url,
                source_title=title,
                evidence_note="Official authentication documentation explicitly references OAuth.",
            )

        if re.search(
            r"\b(?:static\s+)?access\s+tokens?\b",
            lower,
        ):
            add_method("access token")
            add_evidence(
                evidence,
                claim="Access-token authentication is documented.",
                url=url,
                source_title=title,
                evidence_note="Official authentication documentation describes access-token authentication.",
            )

        if re.search(r"\bapi\s+keys?\b|\bhapikey\b", lower):
            add_method("API key")
            add_evidence(
                evidence,
                claim="API-key authentication/access is documented.",
                url=url,
                source_title=title,
                evidence_note="Official authentication documentation references API-key authentication/access.",
            )

        if re.search(r"\bclient[-\s]+credentials?\b", lower):
            add_method("client credentials")
            add_evidence(
                evidence,
                claim="Client-credential authentication is documented.",
                url=url,
                source_title=title,
                evidence_note="Official authentication documentation references client credentials.",
            )

        # Bearer is deliberately NOT added as a separate auth method.
        # It commonly describes how an access token is sent.

    if methods:
        details = (
            "Authentication mechanisms detected from official documentation: "
            + ", ".join(methods)
            + "."
        )
    else:
        details = (
            "No explicit authentication mechanism was detected in the fetched "
            "official authentication sources."
        )

    # We do not infer credential acquisition from the existence of an auth method.
    access_model = "unknown"
    access_details = (
        "Authentication mechanisms were identified, but credential acquisition "
        "has not yet been independently classified from explicit account, "
        "developer-registration, approval, pricing, or access-flow evidence."
    )

    return methods, access_model, access_details



def collect_credential_access(
    record: dict[str, Any],
    evidence: list[Evidence],
) -> tuple[str, str, str | None, str | None]:
    """Classify credential acquisition from explicit official evidence."""
    self_serve_evidence = []
    gated_evidence = []

    self_serve_patterns = [
        r"\bcreate an account\b",
        r"\bcreate a .* account\b",
        r"\bcreate (?:a|an) app\b",
        r"\bcreate and customize\b",
        r"\bcreate a new app\b",
        r"\bpersonal access key\b",
        r"\bapi key\b",
        r"\baccess token\b",
        r"\bdeveloper portal\b",
        r"\bdeveloper platform\b",
        r"\bquickstart\b",
        r"\bget started\b",
    ]

    gated_patterns = [
        r"\bcontact sales\b",
        r"\bsales approval\b",
        r"\bapproval required\b",
        r"\brequires approval\b",
        r"\bpartnership approval\b",
        r"\bpartner approval\b",
        r"\benterprise approval\b",
        r"\bmust be approved by\b",
    ]

    for area, url, title, source_text in iter_sources(record):
        if area != "credential_access":
            continue

        lower = normalize_text(source_text).lower()

        if any(re.search(pattern, lower) for pattern in self_serve_patterns):
            self_serve_evidence.append((url, title))

        if any(re.search(pattern, lower) for pattern in gated_patterns):
            gated_evidence.append((url, title))

    if self_serve_evidence:
        url, title = self_serve_evidence[0]
        add_evidence(
            evidence,
            claim="Developer credentials can be obtained through a documented self-serve flow.",
            url=url,
            source_title=title,
            evidence_note=(
                "Official documentation describes account, app, or credential "
                "creation that a developer can initiate directly."
            ),
        )

    if gated_evidence:
        url, title = gated_evidence[0]
        add_evidence(
            evidence,
            claim="Credential access includes an explicitly gated path.",
            url=url,
            source_title=title,
            evidence_note=(
                "Official documentation explicitly references vendor-controlled "
                "approval or access requirements."
            ),
        )

    if self_serve_evidence and gated_evidence:
        return (
            "mixed",
            "Official evidence shows both self-serve and explicitly gated access paths.",
            None,
            "Vendor-controlled approval is documented for at least one access path.",
        )

    if gated_evidence:
        return (
            "gated",
            "Official evidence indicates vendor-controlled approval is required for credential/access acquisition.",
            None,
            "Vendor-controlled approval or access restriction is explicitly documented.",
        )

    if self_serve_evidence:
        return (
            "self_serve",
            "Official documentation provides a developer-controlled path to obtain credentials without documented sales or partnership approval.",
            None,
            None,
        )

    return (
        "unknown",
        "The fetched official evidence does not establish whether credential acquisition is self-serve or gated.",
        None,
        None,
    )

def collect_api(
    record: dict[str, Any],
    evidence: list[Evidence],
) -> APIAssessment:
    """
    Detect API families from API-focused sources.

    Breadth is deliberately conservative:
    - specialized: one clearly documented API family
    - moderate: multiple distinct families
    - broad: several distinct families spanning materially different domains

    Generic occurrences of words such as "object" or "contact" are not enough
    on their own; the source must be an API-area source and contain recognizable
    API-family terminology.
    """
    family_patterns = [
        ("CRM", [
            r"\bcrm\b",
        ]),
        ("Objects", [
            r"\bobject\s+apis?\b",
            r"\bobject\s+api\b",
            r"\bobjects?\s+api\b",
        ]),
        ("Associations", [
            r"\bassociation(?:s)?\s+api\b",
            r"\bassociation(?:s)?\s+apis\b",
        ]),
        ("Imports", [
            r"\bimports?\s+api\b",
            r"\bimport\s+apis\b",
        ]),
        ("Contacts", [
            r"\bcontacts?\s+api\b",
            r"\bcontacts?\s+apis\b",
        ]),
        ("Companies", [
            r"\bcompanies\s+api\b",
            r"\bcompanies\s+apis\b",
        ]),
        ("Deals", [
            r"\bdeals?\s+api\b",
            r"\bdeals?\s+apis\b",
        ]),
        ("Webhooks", [
            r"\bwebhooks?\b",
        ]),
    ]

    detected: dict[str, list[tuple[str, str | None, str]]] = {}

    for area, url, title, text in iter_sources(record):
        if area != "api":
            continue

        lower = normalize_text(text).lower()

        for family, patterns in family_patterns:
            if any(re.search(pattern, lower) for pattern in patterns):
                detected.setdefault(family, []).append((url, title, text))

    types = list(detected.keys())

    # Keep evidence focused: one representative source per API family.
    for family, sources in detected.items():
        url, title, _ = sources[0]

        add_evidence(
            evidence,
            claim=f"{family} API capabilities are documented.",
            url=url,
            source_title=title,
            evidence_note=(
                f"Official API documentation contains explicit evidence for "
                f"the {family} API family."
            ),
        )

    if len(types) >= 5:
        breadth = "broad"
    elif len(types) >= 2:
        breadth = "moderate"
    elif len(types) == 1:
        breadth = "specialized"
    else:
        breadth = "unknown"

    details = (
        "Distinct API families detected from official API-focused sources: "
        + (", ".join(types) if types else "none")
        + ". Breadth is a conservative first-pass assessment based on "
          "distinct documented API families, not raw keyword frequency."
    )

    return APIAssessment(
        types=types,
        breadth=breadth,
        details=details,
    )


def collect_mcp(
    record: dict[str, Any],
    evidence: list[Evidence],
) -> MCPAssessment:
    """
    Classify MCP using official MCP evidence.

    We distinguish:
    - official_remote: official MCP implementation with remote/hosted evidence
    - official_first_party: official MCP implementation without clear remote evidence
    - none_found: no official MCP evidence found in fetched sources

    'none_found' does not mean MCP does not exist.
    """
    official_mcp_sources = []

    for area, url, title, text in iter_sources(record):
        if area != "mcp":
            continue

        lower = normalize_text(text).lower()

        if not has_phrase(lower, "mcp", "model context protocol"):
            continue

        official_mcp_sources.append((url, title, lower))

    if not official_mcp_sources:
        return MCPAssessment(
            status="none_found",
            details=(
                "No MCP implementation was found in the fetched official "
                "sources. This does not prove that no MCP implementation exists."
            ),
        )

    found_remote = any(
        re.search(
            r"\b(remote|hosted|remote server|remote mcp)\b",
            text,
        )
        for _, _, text in official_mcp_sources
    )

    for url, title, _ in official_mcp_sources:
        add_evidence(
            evidence,
            claim="Official MCP-related documentation was found.",
            url=url,
            source_title=title,
            evidence_note=(
                "Official documentation explicitly references the Model Context "
                "Protocol or an MCP server."
            ),
        )

    if found_remote:
        return MCPAssessment(
            status="official_remote",
            details=(
                "Official documentation contains evidence of a first-party "
                "remote/hosted MCP implementation."
            ),
        )

    return MCPAssessment(
        status="official_first_party",
        details=(
            "Official documentation contains evidence of a first-party MCP "
            "implementation, but the fetched evidence does not establish that "
            "it is remotely hosted."
        ),
    )


def extract_description(
    record: dict[str, Any],
    evidence: list[Evidence],
) -> str:
    """
    Prefer an explicit sentence/paragraph from description-oriented sources.

    Avoid headings such as 'Documentation', 'Overview', etc.
    """
    candidates = []

    for area, url, title, text in iter_sources(record):
        if area != "description":
            continue

        cleaned = normalize_text(text)
    for area, url, title, text in iter_sources(record):
        if area != "description":
            continue

        if not text.strip():
            continue

        # Preserve line boundaries so Markdown headings/navigation text
        # do not get glued to substantive description sentences.
        lines = [
            line.strip(" >#-*")
            for line in text.splitlines()
            if line.strip()
        ]

        sentences = []

        for line in lines:
            if 40 <= len(line) <= 300:
                sentences.append(line)

            # Also split longer prose lines into sentences.
            if len(line) > 300:
                sentences.extend(
                    re.split(r"(?<=[.!?])\s+", line)
                )

        for sentence in sentences:
            sentence = sentence.strip(" -:#>*")
        for sentence in sentences:
            sentence = sentence.strip(" -:#>*")

            if not 40 <= len(sentence) <= 300:
                continue

            lower = sentence.lower()

            if lower in {
                "documentation",
                "overview",
                "getting started",
                "developer documentation",
            }:
                continue

            if "cookie" in lower or "privacy policy" in lower:
                continue

            candidates.append((sentence, url, title))

    if candidates:
        # Prefer substantive product/integration descriptions over
        # documentation-index or navigation-heavy pages.
        def description_score(candidate):
            sentence, url, title = candidate
            score = 0

            title_lower = (title or "").lower()
            sentence_lower = sentence.lower()

            if any(
                phrase in title_lower
                for phrase in (
                    "integrate",
                    "about",
                    "overview",
                    "platform",
                    "product",
                )
            ):
                score += 2

            if any(
                phrase in sentence_lower
                for phrase in (
                    "customer platform",
                    "developer platform",
                    "integration",
                    "platform",
                    "apis",
                    "api library",
                    "build",
                    "connect",
                )
            ):
                score += 1

            if "documentation" in title_lower:
                score -= 2

            if "documentation index" in sentence_lower:
                score -= 3

            return score

        description, url, title = max(
            candidates,
            key=description_score,
        )

        add_evidence(
            evidence,
            claim="A developer-facing description of the app was found.",
            url=url,
            source_title=title,
            evidence_note=(
                "Description selected from an official source using a "
                "content-relevance heuristic that prefers substantive "
                "product/integration descriptions over navigation pages."
            ),
        )

        return description


    app = record["app"]

    return (
        f"{app} provides developer APIs and integration capabilities."
    )


def assess_buildability(
    *,
    auth_methods: list[str],
    access_model: str,
    api: APIAssessment,
    mcp: MCPAssessment,
) -> BuildabilityAssessment:
    """
    Conservative derived assessment.

    This is explicitly an assessment, not a documented fact.

    We only mark 'yes' when the evidence currently supports a plausible
    developer build path. Since credential accessibility is still unknown in
    this first classifier, the result remains constrained/unknown rather than
    pretending that documentation alone proves buildability.
    """
    blockers: list[str] = []

    if not auth_methods:
        blockers.append("No documented authentication mechanism detected.")

    if access_model == "gated":
        blockers.append("Credential access is gated.")

    if access_model == "unknown":
        blockers.append("Credential acquisition/access has not yet been verified.")

    if api.breadth == "unknown":
        blockers.append("API surface has not been sufficiently characterized.")

    if blockers:
        return BuildabilityAssessment(
            verdict="unknown",
            blockers=blockers,
            rationale=(
                "Buildability cannot yet be established because one or more "
                "critical prerequisites remain unverified. This is a derived "
                "assessment rather than a documented vendor claim."
            ),
        )

    return BuildabilityAssessment(
        verdict="yes_with_constraints",
        blockers=[],
        rationale=(
            "The documented authentication and API surface support a plausible "
            "integration path, subject to permissions, plan limits, rate limits, "
            "and runtime testing."
        ),
    )


def build_record(record: dict[str, Any]) -> AppResearchRecord:
    evidence: list[Evidence] = []

    app = record["app"]
    domain = record.get("domain", "")
    category = record.get("category", "")

    auth_methods, access_model, access_details = collect_authentication(
        record,
        evidence,
    )

    (
        credential_access_model,
        credential_access_details,
        plan_requirement,
        approval_requirement,
    ) = collect_credential_access(
        record,
        evidence,
    )

    api = collect_api(record, evidence)
    mcp = collect_mcp(record, evidence)
    description = extract_description(record, evidence)

    buildability = assess_buildability(
        auth_methods=auth_methods,
        access_model=credential_access_model,
        api=api,
        mcp=mcp,
    )

    confidence = Confidence(
        overall="medium" if evidence else "low",
        auth="high" if auth_methods else "low",
        credential_access=(
            "high"
            if credential_access_model != "unknown"
            else "low"
        ),
        api="high" if api.types else "low",
        mcp="high" if mcp.status != "none_found" else "medium",
        buildability="low",
    )

    verification = Verification(
        status="unverified",
        verifier_agrees=None,
        human_verified=False,
        notes=(
            "Baseline classifier output. Independent verification has not yet "
            "been performed."
        ),
    )

    return AppResearchRecord(
        app=app,
        domain=domain,
        category=category,
        description=description,
        auth_methods=auth_methods,
        access=AccessAssessment(
            model=credential_access_model,
            details=credential_access_details,
            plan_requirement=plan_requirement,
            approval_requirement=approval_requirement,
        ),
        api=api,
        mcp=mcp,
        buildability=buildability,
        evidence=evidence,
        confidence=confidence,
        verification=verification,
    )


def main() -> None:
    research = load_research()

    records = []

    for record in research:
        print(f"[classify] {record['app']}")
        structured = build_record(record)
        records.append(structured.model_dump(mode="json"))

    save_records(records)

    print()
    print(f"Saved {len(records)} classified record(s)")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
