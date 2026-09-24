# Composio AI Product Ops Take-home

## Researching 100 apps with an evidence-first agent

This project builds a reproducible research pipeline for evaluating 100 apps across 10 categories.

The goal is not simply to collect app metadata. The pipeline separates:

1. Source discovery
2. Evidence collection
3. Structured classification
4. Verification
5. Pattern analysis
6. Human review

The system deliberately preserves uncertainty instead of filling missing evidence with guesses.

## What was researched

For each app, the pipeline investigates:

- App description
- Authentication methods
- Credential access model
- API surface and breadth
- MCP availability
- Buildability for an integration
- Evidence supporting the classifications

The 100 apps are distributed across 10 categories.

## Evidence-first approach

The core design principle is:

> Claim → source → evidence → interpretation → classification

Search results are treated primarily as discovery signals. When possible, official developer/API documentation is promoted to the evidence layer.

The pipeline does not treat a search failure as proof that a capability does not exist.

For example:

- `none_found` for MCP means no official MCP evidence was found in the searched sources.
- `unknown` means the available evidence was insufficient for a defensible classification.
- `yes_with_constraints` means the documented evidence suggests an integration path exists, while recognizing permissions, plan limits, rate limits, and runtime validation.

## Architecture

    100-app seed
         |
         v
    Research orchestrator
         |
         +-- Description search
         +-- Authentication search
         +-- Credential-access search
         +-- API search
         +-- MCP search
         |
         v
    Official-source evidence
         |
         v
    Structured classifier
         |
         +-- Auth
         +-- Credential access
         +-- API breadth
         +-- MCP
         +-- Buildability
         |
         v
    First-pass dataset
         |
         v
    Independent verification search
         |
         v
    Failure analysis + human review points
         |
         v
    Case-study report

## Repository structure

    composio-takehome/
    ├── data/
    │   ├── raw/
    │   │   └── apps.json
    │   ├── processed/
    │   │   └── first_pass.json
    │   └── verified/
    │       ├── sample20.json
    │       ├── second_pass.json
    │       └── human_verification.json
    ├── docs/
    │   └── research-rules.md
    ├── prompts/
    ├── reports/
    │   └── case-study.html
    ├── src/
    │   ├── schema.py
    │   ├── researcher.py
    │   ├── classifier.py
    │   ├── run_classifier.py
    │   ├── verifier.py
    │   ├── verify_pass.py
    │   ├── analyze.py
    │   └── build_report.py
    ├── tests/
    ├── .env.example
    ├── .gitignore
    └── README.md

## Classification definitions

### Credential access

`self_serve`

A developer can independently obtain credentials through a documented developer/account flow without documented sales, partnership, or external approval.

`gated`

Access requires a documented sales, partnership, enterprise, or approval process that the developer cannot independently complete.

`mixed`

Meaningful capabilities have different access models.

`unknown`

The available evidence is insufficient.

### MCP

The pipeline distinguishes:

- `official_first_party`
- `official_hosted`
- `official_remote`
- `third_party`
- `community`
- `self_hosted`
- `none_found`
- `unknown`

`none_found` is intentionally not interpreted as proof that an MCP implementation does not exist.

### API breadth

API breadth is an assessment derived from documented API families rather than endpoint-count keyword frequency.

Possible values:

- `broad`
- `moderate`
- `narrow`
- `specialized`
- `unknown`

### Buildability

Buildability is a derived assessment, not a vendor-documented fact.

Possible values:

- `yes`
- `yes_with_constraints`
- `blocked`
- `unknown`

The assessment considers authentication, credential accessibility, API evidence, permissions, plan requirements, rate limits, events/webhooks, and related constraints.

## Verification

The first pass was followed by an independent second-pass search across 20 apps, with two apps sampled from each category.

The verification pass was intentionally separated from the initial classifier so that it could expose retrieval and classification failures.

One clear failure mode was API-breadth detection.

The first-pass taxonomy relied on a relatively small set of API-family keywords. Independent verification showed that this could produce overly conservative `unknown` or narrow classifications when official documentation exposed substantially richer API surfaces.

This is treated as a system failure to improve, not hidden.

### Why there is no fabricated accuracy percentage

The current verification dataset contains independent verification searches, but it does not contain complete field-level human ground-truth labels for all 20 sampled apps.

Therefore this project does not claim a made-up accuracy percentage.

A production version should store explicit human labels for each verified field and calculate:

- precision
- recall
- agreement
- field-level error rates
- confidence calibration

## Human-in-the-loop areas

Human review remains particularly valuable for:

- Ambiguous official domains
- Vendor-specific credential requirements
- Plan and permission restrictions
- Distinguishing absence of MCP evidence from actual absence
- Judging meaningful API breadth
- Low-confidence records
- Final build/outreach decisions

The goal is not to remove humans from the process. It is to spend human attention where automated research has the highest uncertainty or business impact.

## Running the pipeline

Create a virtual environment and install dependencies:

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

Configure environment variables using `.env`:

    COMPOSIO_API_KEY=...
    OPENAI_API_KEY=...

Never commit `.env`.

### 1. Research

    python src/researcher.py

Produces:

    data/raw/research_evidence.json

The raw evidence file is generated locally during research and is intentionally
excluded from the public repository because fetched vendor documentation can
contain credential-like examples. The processed and verified outputs are
included for reproducibility and review.

### 2. Classify

    python -m src.run_classifier

Produces:

    data/processed/first_pass.json

### 3. Verification

    python src/verify_pass.py

Produces:

    data/verified/second_pass.json

### 4. Report

    python src/build_report.py

Produces:

    reports/case-study.html

## Current output

The pipeline successfully processes all 100 seeded apps into the first-pass structured dataset.

The case study presents:

- First-pass distributions
- Category-level patterns
- The research workflow
- The independent verification pass
- Observed failure modes
- Human-review requirements
- The complete 100-app research matrix
- Evidence links where available
- Reproduction commands

Open `reports/case-study.html` for the complete case study.

## Important limitations

This is a time-boxed research system rather than a claim of production-grade exhaustive web intelligence.

Important limitations include:

- Search coverage can miss documentation.
- Vendor documentation changes over time.
- API breadth classification is taxonomy-dependent.
- Credential requirements can vary by plan, account type, geography, or product tier.
- MCP discovery is evidence-based rather than an exhaustive registry.
- Buildability is an assessment and requires runtime validation before production use.
- The first-pass credential classifier uses evidence patterns and therefore requires verification for ambiguous cases.

These limitations are preserved because making them visible is more useful than presenting false certainty.

## Design principle

The central product lesson from the exercise is:

> Automated research creates scale. Verification creates trust.

The useful system is therefore not an agent that confidently fills 100 rows. It is a pipeline that can show:

- what it found,
- where it found it,
- why it classified something,
- what it could not establish,
- where it failed,
- and where a human should intervene.

## Take-home report

The self-contained case study is available at:

    reports/case-study.html
