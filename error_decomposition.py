
import csv
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "results" / "tables" / "s3_scan.csv"
OUTPUT = ROOT / "results" / "tables" / "error_decomposition.csv"
FIGURE = ROOT / "results" / "figures" / "error_decomposition.png"

with INPUT.open(newline="") as f:
    data = list(csv.DictReader(f))

rows = []

for row in data:
    ideal = float(row["fidelity_trotter_ideal"])
    noisy = float(row["fidelity_noisy"])

    trotter_error = 1 - ideal
    noise_loss = ideal - noisy
    total_error = 1 - noisy

    assert abs(
        total_error - (trotter_error + noise_loss)
    ) < 1e-10

    rows.append({
        "processor": row["processor"],
        "noise_scale": row["noise_scale"],
        "steps": int(row["steps"]),
        "trotter_error": trotter_error,
        "noise_loss": noise_loss,
        "total_error": total_error,
    })

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

fields = [
    "processor", "noise_scale", "steps",
    "trotter_error", "noise_loss", "total_error"
]

with OUTPUT.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

selected = sorted(
    (
        row for row in rows
        if row["processor"] == "D"
        and float(row["noise_scale"]) == 1.0
    ),
    key=lambda row: row["steps"]
)

steps = [row["steps"] for row in selected]

plt.figure(figsize=(10, 6))

plt.plot(
    steps,
    [row["trotter_error"] for row in selected],
    "o-",
    label="Trotter approximation error"
)

plt.plot(
    steps,
    [row["noise_loss"] for row in selected],
    "s-",
    label="Noise-induced fidelity loss"
)

plt.plot(
    steps,
    [row["total_error"] for row in selected],
    "^-",
    label="Total infidelity"
)

plt.xlabel("Number of Trotter steps")
plt.ylabel("Error / fidelity loss")
plt.title("Q-OPTIMA: Error Decomposition — Processor D (1x)")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

FIGURE.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(FIGURE, dpi=200)
plt.close()

best = min(selected, key=lambda row: row["total_error"])

print("PASS: Error decomposition completed")
print(f"Rows analyzed: {len(rows)}")
print(f"Processor D optimal steps at 1x: {best['steps']}")
print(f"Minimum total infidelity: {best['total_error']:.6f}")
print(f"Saved table: {OUTPUT}")
print(f"Saved graph: {FIGURE}")
