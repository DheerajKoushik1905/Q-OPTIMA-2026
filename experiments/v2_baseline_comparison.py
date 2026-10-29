
import csv
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "results" / "tables"
OUTPUT = TABLES / "v2_baseline_comparison.csv"

with (TABLES / "advisor_final_validation.csv").open(
    newline=""
) as f:
    advisor = list(csv.DictReader(f))

# Fresh-validation fidelity values, previously generated
# by final_advisor_test.py, were not saved as a scan CSV.
# Use the saved summary's optimal fidelity regret to
# evaluate advisor models, and rerun the exact scan only
# if fixed-step comparisons need fidelity values.

models = ["linear", "quadratic"]
summary = []

for model in models:
    rows = [r for r in advisor if r["model"] == model]

    assert len(rows) == 5, (
        f"Expected 5 validation rows for {model}"
    )

    summary.append({
        "strategy": model,
        "exact_matches": sum(
            int(r["exact_match"]) for r in rows
        ),
        "mean_fidelity_regret": mean(
            float(r["fidelity_regret"]) for r in rows
        ),
    })

print("Q-OPTIMA V2 — VERIFIED ADVISOR BASELINES")
print("=" * 65)

for row in summary:
    print(
        f"{row['strategy']:12s} | "
        f"Exact matches: {row['exact_matches']}/5 | "
        f"Mean regret: {row['mean_fidelity_regret']:.6f}"
    )

print()
print(
    "NOTE: Fixed-step baselines require the full fidelity "
    "scan for the fresh validation noise settings."
)
print(
    "This script verifies the saved advisor results "
    "without inventing missing fidelity values."
)
