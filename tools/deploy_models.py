"""Deploys the three models Content Understanding and Tarikh need into your Foundry resource, using the Azure CLI.

Run:  python -m tools.deploy_models --account <foundry-resource-name> --group <resource-group>
Deployment names equal the model names (gpt-4.1, gpt-4.1-mini, text-embedding-3-large), which is what .env expects.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

WANTED = ("gpt-4.1", "gpt-4.1-mini", "text-embedding-3-large")
CAP = 50  # thousand tokens per minute; keeps well inside a student subscription's quota


def plan_deployments(listed: list[dict]) -> list[dict]:
    plan = []
    for name in WANTED:
        options = [m for m in listed if m.get("name") == name and m.get("format") == "OpenAI"]
        if not options:
            raise LookupError(f"{name} is not offered by this resource in its region. Pick another region (docs/azure-setup.md, step 3).")
        best = max(options, key=lambda m: m["version"])
        skus = {s["name"]: s for s in best.get("skus", [])}
        sku = "GlobalStandard" if "GlobalStandard" in skus else next(iter(skus))
        default = (skus[sku].get("capacity") or {}).get("default") or CAP
        plan.append({"deployment": name, "model": name, "version": best["version"], "sku": sku, "capacity": min(default, CAP)})
    return plan


def az(*args: str) -> str:
    out = subprocess.run(["az", *args], capture_output=True, text=True, shell=(sys.platform == "win32"))
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or "az failed")
    return out.stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", required=True, help="the Foundry resource name (first part of your project endpoint)")
    ap.add_argument("--group", required=True, help="its resource group")
    a = ap.parse_args()
    try:
        listed = json.loads(az("cognitiveservices", "account", "list-models", "-n", a.account, "-g", a.group, "-o", "json"))
        plan = plan_deployments(listed)
    except (RuntimeError, LookupError) as exc:
        print(f"Could not plan the deployments: {exc}")
        return 1
    existing = {d["name"] for d in json.loads(az("cognitiveservices", "account", "deployment", "list", "-n", a.account, "-g", a.group, "-o", "json"))}
    for p in plan:
        if p["deployment"] in existing:
            print(f"already deployed: {p['deployment']}")
            continue
        print(f"deploying {p['deployment']} {p['version']} ({p['sku']}, capacity {p['capacity']}) ...", flush=True)
        try:
            az("cognitiveservices", "account", "deployment", "create", "-n", a.account, "-g", a.group,
               "--deployment-name", p["deployment"], "--model-name", p["model"], "--model-version", p["version"],
               "--model-format", "OpenAI", "--sku-name", p["sku"], "--sku-capacity", str(p["capacity"]))
        except RuntimeError as exc:
            print(f"  failed: {exc}\n  If this mentions quota, deploy it in the Foundry portal with a smaller capacity.")
            return 1
    print("Done. In .env set AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4.1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
