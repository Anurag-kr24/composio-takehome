import json
import time
from pathlib import Path
from composio import Composio
from dotenv import load_dotenv

load_dotenv()

VERSION = "20260903_00"

SEARCH = "COMPOSIO_SEARCH_WEB"

with open("data/verified/sample20.json") as f:
    sample = json.load(f)

client = Composio()

results = []

for i, app in enumerate(sample, 1):
    name = app["app"]

    query = (
        f"{name} official developer documentation "
        f"authentication API MCP credentials"
    )

    print(f"[{i}/20] {name}", flush=True)

    result = client.tools.execute(
        slug=SEARCH,
        version=VERSION,
        arguments={"query": query},
    )

    results.append({
        "app": name,
        "category": app["category"],
        "first_pass": {
            "access": app["access"],
            "api": app["api"],
            "mcp": app["mcp"],
            "buildability": app["buildability"],
        },
        "verification_search": result,
    })

    time.sleep(0.5)

out = Path("data/verified/second_pass.json")
with out.open("w") as f:
    json.dump(results, f, indent=2)

print("Saved:", out)
