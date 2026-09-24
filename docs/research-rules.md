# Composio App Research Rules

## Evidence hierarchy

1. Official developer/API documentation
2. Official product/developer documentation
3. Official GitHub repository
4. Official engineering/developer blog
5. Official support documentation
6. Reputable secondary source
7. Search-result snippets only for discovery, never as final evidence

Official evidence should be preferred for material claims.

---

## Self-serve

SELF_SERVE means a developer can independently obtain the relevant credentials through a documented developer/account flow without contacting sales or requiring external partnership approval.

A free account is not required. Paid self-serve access can still be self-serve.

---

## Gated

GATED means relevant API credentials/access require one or more of:

- contacting sales
- partnership approval
- enterprise contract
- external approval
- another access process that the developer cannot independently complete

---

## Mixed

MIXED means some meaningful API capabilities are self-serve while other capabilities require elevated access, payment, approval, enterprise access, or partnership.

---

## Unknown

UNKNOWN means the available evidence is insufficient to make a defensible classification.

Do not infer self-serve merely because API documentation exists.

---

## Authentication

Distinguish:

- OAuth2
- API key
- bearer token
- personal access token
- basic authentication
- service account
- custom/other

Do not collapse every bearer token into "API key".

---

## MCP

MCP classification:

- official_first_party
- official_hosted
- official_remote
- third_party
- community
- self_hosted
- none_found
- unknown

"none_found" means the research process did not find MCP evidence in the defined search scope.

It does NOT prove that no MCP implementation exists anywhere.

---

## API breadth

BROAD:
Multiple major resource families/actions with meaningful CRUD or operational coverage.

MODERATE:
Several useful resource families but notable gaps.

NARROW:
Limited/specialized API surface.

SPECIALIZED:
Purpose-built API where breadth is not naturally comparable to a general SaaS API.

UNKNOWN:
Insufficient evidence.

---

## Buildability

YES:
Accessible credentials, documented API, sufficient surface, and no major blocker identified.

YES_WITH_CONSTRAINTS:
Buildable but meaningful limitations exist.

BLOCKED:
A material blocker prevents a practical toolkit without additional access, partnership, or major workaround.

UNKNOWN:
Evidence is insufficient for a defensible assessment.

Buildability is an assessment, not a directly documented fact.

---

## Evidence rule

Every material classification should have supporting evidence.

The system must never invent:

- URLs
- source titles
- quotations
- API capabilities
- MCP availability
- credential requirements

If evidence is insufficient, return UNKNOWN.

---

## Verification rule

A verifier must independently evaluate whether evidence supports the claim.

A source merely mentioning a concept does not automatically establish the classification.

Human verification is required for the final audit sample.
