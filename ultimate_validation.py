
import csv
from pathlib import Path

TABLES = Path(__file__).resolve().parent / "results" / "tables"

def load(name):
    with (TABLES / name).open(
        newline="", encoding="utf-8-sig"
    ) as f:
        return list(csv.DictReader(f))

predictions = load("ultimate_predictions.csv")
reference = load("advisor_final_validation.csv")
scan = load("v2_fixed_step_scan.csv")

# One actual optimum per noise scale.
actual = {}
for row in reference:
    scale = float(row["noise_scale"])
    actual[scale] = int(row["actual_optimal_steps"])

# Actual simulated fidelities for calculating regret.
fidelity = {}
for row in scan:
    scale = float(row["noise_scale"])
    steps = int(row["steps"])
    fidelity[(scale, steps)] = float(row["fidelity"])

# Select Ultimate's highest-ranked Processor D prediction.
ultimate = {}
for row in predictions:
    if row["processor"] != "D":
        continue

    scale = float(row["noise_scale"])
    if scale not in actual:
        continue

    if scale not in ultimate:
        ultimate[scale] = int(row["steps"])

results = []

for scale in sorted(actual):
    predicted = ultimate[scale]
    optimal = actual[scale]

    best_fidelity = fidelity[(scale, optimal)]
    predicted_fidelity = fidelity[(scale, predicted)]

    regret = best_fidelity - predicted_fidelity

    results.append({
        "noise_scale": scale,
        "predicted_steps": predicted,
        "actual_optimal_steps": optimal,
        "exact_match": int(predicted == optimal),
        "fidelity_regret": regret,
    })

output = TABLES / "ultimate_validation.csv"

with output.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f, fieldnames=list(results[0].keys())
    )
    writer.writeheader()
    writer.writerows(results)

matches = sum(r["exact_match"] for r in results)
mean_regret = sum(r["fidelity_regret"] for r in results) / len(results)

print("\nQ-OPTIMA ULTIMATE — VALIDATION")
print("=" * 50)

for r in results:
    print(
        f"Noise {r['noise_scale']:.2f}x | "
        f"Predicted {r['predicted_steps']:>2} | "
        f"Actual {r['actual_optimal_steps']:>2} | "
        f"Regret {r['fidelity_regret']:.6f}"
    )

print(f"\nExact matches: {matches}/{len(results)}")
print(f"Mean fidelity regret: {mean_regret:.6f}")
print(f"Saved: {output}")
