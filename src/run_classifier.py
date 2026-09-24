import json
from pathlib import Path

from src.classifier import build_record

ROOT = Path(__file__).resolve().parent.parent

with open(ROOT / "data/raw/research_evidence.json") as f:
    evidence = json.load(f)

results = []

for i, item in enumerate(evidence, 1):
    print(f"[{i}/{len(evidence)}] {item['app']}", flush=True)
    results.append(build_record(item).model_dump(mode="json"))

out = ROOT / "data/processed/first_pass.json"
out.parent.mkdir(parents=True, exist_ok=True)

with out.open("w") as f:
    json.dump(results, f, indent=2)

print(f"Saved: {out}")
print(f"Records: {len(results)}")
