import json
from pathlib import Path
from collections import Counter, defaultdict
from html import escape

ROOT = Path(__file__).resolve().parent.parent

with open(ROOT / "data/processed/first_pass.json") as f:
    data = json.load(f)

with open(ROOT / "data/verified/second_pass.json") as f:
    verification = json.load(f)

def counts(field, subfield):
    return Counter(
        r.get(field, {}).get(subfield)
        for r in data
        if r.get(field, {}).get(subfield) is not None
    )

access = counts("access", "model")
build = counts("buildability", "verdict")
mcp = counts("mcp", "status")
api = counts("api", "breadth")

categories = defaultdict(list)
for r in data:
    categories[r["category"]].append(r)

def bar_row(label, value, total=100):
    pct = round(value / total * 100)
    return f"""
    <div class="barrow">
      <div class="barlabel"><span>{escape(str(label))}</span><b>{value}</b></div>
      <div class="bar"><i style="width:{pct}%"></i></div>
    </div>
    """

def pill(value):
    return f'<span class="pill">{escape(str(value))}</span>'

rows = []

for r in data:
    evidence = r.get("evidence", [])
    urls = []
    for e in evidence:
        if e.get("url") and e["url"] not in urls:
            urls.append(e["url"])

    rows.append(f"""
    <tr>
      <td><b>{escape(r["app"])}</b></td>
      <td>{escape(r["category"])}</td>
      <td>{pill(", ".join(r.get("auth_methods", [])) or "unknown")}</td>
      <td>{pill(r.get("access", {}).get("model", "unknown"))}</td>
      <td>{pill(r.get("api", {}).get("breadth", "unknown"))}</td>
      <td>{pill(r.get("mcp", {}).get("status", "unknown"))}</td>
      <td>{pill(r.get("buildability", {}).get("verdict", "unknown"))}</td>
      <td>
        {" ".join(
          f'<a href="{escape(u)}" target="_blank">source</a>'
          for u in urls[:3]
        ) or "—"}
      </td>
    </tr>
    """)

category_rows = []
for cat in sorted(categories):
    items = categories[cat]
    selfserve = sum(x.get("access", {}).get("model") == "self_serve" for x in items)
    buildable = sum(x.get("buildability", {}).get("verdict") == "yes_with_constraints" for x in items)
    mcp_count = sum(x.get("mcp", {}).get("status") != "none_found" for x in items)

    category_rows.append(f"""
    <tr>
      <td><b>{escape(cat)}</b></td>
      <td>{len(items)}</td>
      <td>{selfserve}</td>
      <td>{buildable}</td>
      <td>{mcp_count}</td>
    </tr>
    """)

unknown_apps = [
    r["app"] for r in data
    if "unknown" in {
        r.get("access", {}).get("model"),
        r.get("api", {}).get("breadth"),
        r.get("buildability", {}).get("verdict")
    }
]

html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Composio AI Product Ops Take-home — App Research Agent</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#f5f6f8;color:#17191d;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.45}}
main{{max-width:1400px;margin:auto;padding:48px 34px 80px}}
.hero{{background:#111318;color:white;border-radius:24px;padding:42px;margin-bottom:24px}}
.kicker{{font-size:13px;text-transform:uppercase;letter-spacing:.14em;opacity:.65;font-weight:700}}
h1{{font-size:48px;line-height:1.02;margin:12px 0 18px;max-width:900px}}
h2{{font-size:28px;margin:0 0 18px}}
h3{{margin-bottom:8px}}
.lead{{font-size:19px;max-width:850px;color:#cdd1d8}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:20px 0}}
.card{{background:white;border:1px solid #e2e5e9;border-radius:16px;padding:20px}}
.big{{font-size:36px;font-weight:800}}
.muted{{color:#6b7078}}
section{{background:white;border:1px solid #e2e5e9;border-radius:20px;padding:28px;margin:20px 0}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}
.barrow{{margin:12px 0}}
.barlabel{{display:flex;justify-content:space-between;font-size:14px;margin-bottom:5px}}
.bar{{height:9px;background:#e8eaed;border-radius:20px;overflow:hidden}}
.bar i{{display:block;height:100%;background:#20242b;border-radius:20px}}
table{{border-collapse:collapse;width:100%;font-size:13px}}
th{{text-align:left;background:#f0f2f4;position:sticky;top:0}}
td,th{{padding:10px 9px;border-bottom:1px solid #e6e8eb;vertical-align:top}}
.pill{{display:inline-block;padding:3px 7px;border-radius:999px;background:#eef0f2;margin:1px;font-size:11px}}
.workflow{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}}
.step{{padding:16px;border:1px solid #dddfe3;border-radius:14px;background:#fafafa}}
.num{{font-weight:800;font-size:12px;color:#777}}
.insight{{padding:16px;border-left:4px solid #20242b;background:#f7f7f8;border-radius:8px;margin:10px 0}}
.small{{font-size:12px}}
a{{color:#2358a6}}
footer{{color:#777;font-size:12px;margin-top:30px}}
@media(max-width:900px){{.grid,.cols,.workflow{{grid-template-columns:1fr 1fr}}h1{{font-size:38px}}}}
@media(max-width:600px){{.grid,.cols,.workflow{{grid-template-columns:1fr}}main{{padding:20px}}}}
</style>
</head>
<body>
<main>

<div class="hero">
<div class="kicker">Composio · AI Product Ops Intern</div>
<h1>Researching 100 apps with an evidence-first agent</h1>
<p class="lead">
A reproducible pipeline searched official developer sources, fetched evidence,
classified auth/access/API/MCP/buildability, and then ran an independent
20-app verification search pass. The key lesson: automated discovery is fast;
verification is where the useful product signal appears.
</p>
</div>

<div class="grid">
<div class="card"><div class="muted">Apps researched</div><div class="big">100</div></div>
<div class="card"><div class="muted">Categories</div><div class="big">10</div></div>
<div class="card"><div class="muted">First-pass records</div><div class="big">100</div></div>
<div class="card"><div class="muted">Verification sample</div><div class="big">20</div></div>
</div>

<section>
<h2>Headline findings</h2>
<div class="insight"><b>1. Self-serve dominates the first pass.</b> 79/100 were classified self-serve, but 17 remained unknown and 4 mixed. This is a first-pass signal, not a final ground-truth rate.</div>
<div class="insight"><b>2. API breadth is the weakest automated field.</b> 42/100 were unknown and only 1 was classified broad. Independent verification immediately exposed false "unknown" cases: Shopify and Zendesk, for example, have extensive documented API surfaces.</div>
<div class="insight"><b>3. MCP is increasingly common but evidence quality matters.</b> 39 apps had official-remote MCP evidence and 17 first-party MCP evidence in the first pass. "none_found" means no official evidence was found in the searched sources — not proof that an MCP does not exist.</div>
<div class="insight"><b>4. Buildability is deliberately conservative.</b> 53 were "yes_with_constraints"; 47 stayed unknown because missing auth/API evidence prevented a defensible buildability conclusion.</div>
</section>

<section>
<h2>First-pass distribution</h2>
<div class="cols">
<div>
<h3>Credential access</h3>
{"".join(bar_row(k,v) for k,v in access.items())}
</div>
<div>
<h3>Buildability</h3>
{"".join(bar_row(k,v) for k,v in build.items())}
</div>
<div>
<h3>MCP evidence</h3>
{"".join(bar_row(k,v) for k,v in mcp.items())}
</div>
<div>
<h3>API breadth</h3>
{"".join(bar_row(k,v) for k,v in api.items())}
</div>
</div>
</section>

<section>
<h2>Agent / research workflow</h2>
<div class="workflow">
<div class="step"><div class="num">01 · SEED</div><h3>100 apps</h3><p>Canonical assignment list with category and official-domain hints.</p></div>
<div class="step"><div class="num">02 · SEARCH</div><h3>5 evidence areas</h3><p>Description, authentication, credential access, API, MCP.</p></div>
<div class="step"><div class="num">03 · FETCH</div><h3>Official sources</h3><p>Search citations are discovery; official-domain pages are promoted as evidence.</p></div>
<div class="step"><div class="num">04 · CLASSIFY</div><h3>Structured record</h3><p>Pydantic schema produces reproducible classifications and uncertainty.</p></div>
<div class="step"><div class="num">05 · VERIFY</div><h3>20-app second pass</h3><p>Two apps per category are independently re-searched to expose misses.</p></div>
</div>
</section>

<section>
<h2>Verification: what changed the system</h2>
<p>
The independent verification pass covered <b>{len(verification)}</b> apps, two per category.
It was intentionally separated from the first-pass classifier.
</p>
<div class="insight">
<b>Observed failure mode:</b> API breadth was systematically under-detected.
The first-pass classifier relied on a small family of API keywords. Official docs show
much richer surfaces than those keywords captured.
</div>
<div class="insight">
<b>Example — Shopify:</b> first pass = API breadth <b>unknown</b>.
Official documentation exposes GraphQL Admin, Storefront and REST APIs, plus
webhooks and other platform capabilities. This is a classifier recall failure,
not a lack of Shopify API documentation.
</div>
<div class="insight">
<b>Example — Zendesk:</b> first pass = API breadth <b>moderate</b>.
Official documentation spans ticketing, Help Center, messaging, voice, AI Agents,
custom data, omnichannel and Sales CRM. The verification pass therefore flags
the API taxonomy as too conservative.
</div>
<p class="small muted">
Important: the verification pass is evidence-based and intentionally does not turn
search agreement into a fabricated "accuracy %" metric. A future production version
would store field-level human labels and compute precision/recall per field.
</p>
</section>

<section>
<h2>Where the agent needed a human</h2>
<ul>
<li>Resolving ambiguous or missing official domains, e.g. Paygent Connect.</li>
<li>Distinguishing "no MCP evidence found" from "no MCP exists."</li>
<li>Judging whether API families are materially broad versus merely many endpoints.</li>
<li>Interpreting vendor-specific admin/plan/access requirements.</li>
<li>Reviewing low-confidence cases before making outreach/build decisions.</li>
</ul>
</section>

<section>
<h2>Category matrix</h2>
<table>
<thead><tr><th>Category</th><th>Apps</th><th>Self-serve</th><th>Buildable*</th><th>MCP evidence</th></tr></thead>
<tbody>
{"".join(category_rows)}
</tbody>
</table>
<p class="small muted">* "Buildable" means the first-pass verdict was yes_with_constraints; it is not a claim that production integration is already validated.</p>
</section>

<section>
<h2>Research matrix — all 100 apps</h2>
<div style="max-height:720px;overflow:auto">
<table>
<thead>
<tr>
<th>App</th><th>Category</th><th>Auth</th><th>Access</th><th>API</th><th>MCP</th><th>Buildability</th><th>Evidence</th>
</tr>
</thead>
<tbody>
{"".join(rows)}
</tbody>
</table>
</div>
</section>

<section>
<h2>Reproduce</h2>
<pre style="white-space:pre-wrap;background:#111318;color:#eee;padding:18px;border-radius:12px">python src/researcher.py
python -m src.run_classifier
python src/verify_pass.py
python src/build_report.py</pre>
<p>
Source files: <code>src/researcher.py</code>, <code>src/classifier.py</code>,
<code>src/verify_pass.py</code>. Raw evidence is generated locally at
<code>data/raw/research_evidence.json</code> and intentionally excluded from
the public repository because fetched vendor documentation can contain
credential-like examples. The processed and verified outputs are included
for review and reproducibility.
</p>
</section>

<footer>
Built as a time-boxed take-home. The system prefers explicit uncertainty over invented evidence.
"none_found" and "unknown" are intentionally preserved where the evidence pipeline could not establish a claim.
</footer>

</main>
</body>
</html>
"""

out = ROOT / "reports" / "case-study.html"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html, encoding="utf-8")

print("Created:", out)
print("Size:", out.stat().st_size, "bytes")
