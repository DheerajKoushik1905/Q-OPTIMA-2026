
import csv
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "results" / "tables" / "s3_scan.csv"
OUTPUT = ROOT / "results" / "tables" / "advisor_results.csv"

with INPUT.open(newline="") as f:
    rows = list(csv.DictReader(f))

# We use Processor D to study noise sensitivity.
data = [
    r for r in rows
    if r["processor"] == "D"
]

steps = sorted({int(r["steps"]) for r in data})
scales = sorted({float(r["noise_scale"]) for r in data})

# Approximation error from ideal simulations.
ideal_error = {
    int(r["steps"]): 1.0 - float(r["fidelity_trotter_ideal"])
    for r in data
}

# Train the noise-cost coefficient using only 1x data.
training = [
    r for r in data
    if float(r["noise_scale"]) == 1.0
]

# Simple interpretable model:
# predicted total error = ideal error + alpha * noise_scale * steps
#
# This is an approximation, not an exact physical noise model.
noise_losses = np.array([
    float(r["fidelity_trotter_ideal"])
    - float(r["fidelity_noisy"])
    for r in training
])

step_values = np.array([
    int(r["steps"]) for r in training
], dtype=float)

alpha = float(
    np.dot(step_values, noise_losses)
    / np.dot(step_values, step_values)
)

print(f"Learned noise coefficient alpha = {alpha:.8f}")

results = []

for scale in scales:
    candidates = []

    for n in steps:
        predicted_error = (
            ideal_error[n]
            + alpha * scale * n
        )
        candidates.append((n, predicted_error))

    predicted_n = min(candidates, key=lambda x: x[1])[0]

    actual = [
        r for r in data
        if float(r["noise_scale"]) == scale
    ]

    best = max(
        actual,
        key=lambda r: float(r["fidelity_noisy"])
    )

    actual_n = int(best["steps"])

    predicted_row = next(
        r for r in actual
        if int(r["steps"]) == predicted_n
    )

    fidelity_at_prediction = float(
        predicted_row["fidelity_noisy"]
    )
    optimal_fidelity = float(best["fidelity_noisy"])

    regret = optimal_fidelity - fidelity_at_prediction

    results.append({
        "noise_scale": scale,
        "predicted_steps": predicted_n,
        "actual_optimal_steps": actual_n,
        "fidelity_at_prediction": fidelity_at_prediction,
        "optimal_fidelity": optimal_fidelity,
        "fidelity_regret": regret,
    })

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=list(results[0].keys())
    )
    writer.writeheader()
    writer.writerows(results)

print()
print("Q-OPTIMA ADVISOR RESULTS")
print("-" * 70)

for r in results:
    print(
        f"Noise {r['noise_scale']}x | "
        f"Predicted n={r['predicted_steps']} | "
        f"Actual n*={r['actual_optimal_steps']} | "
        f"Fidelity regret={r['fidelity_regret']:.6f}"
    )

print()
print(f"Saved: {OUTPUT}")
