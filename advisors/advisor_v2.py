
import csv
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "results" / "tables"

def read_csv(name):
    with (TABLES / name).open(newline="") as f:
        return list(csv.DictReader(f))

original = read_csv("s3_scan.csv")
holdout = read_csv("advisor_holdout_scan.csv")

training = sorted(
    [
        r for r in original
        if r["processor"] == "D"
        and float(r["noise_scale"]) == 1.0
    ],
    key=lambda r: int(r["steps"])
)

assert len(training) == 12

steps = np.array(
    [int(r["steps"]) for r in training],
    dtype=int
)

ideal_error = np.array([
    1.0 - float(r["fidelity_trotter_ideal"])
    for r in training
])

gate_counts = np.array([
    float(r["two_q"]) for r in training
])

noise_loss = np.array([
    float(r["fidelity_trotter_ideal"])
    - float(r["fidelity_noisy"])
    for r in training
])

# Fit a nonnegative noise-loss coefficient.
def fit_coefficient(cost):
    denominator = float(np.dot(cost, cost))
    return max(
        0.0,
        float(np.dot(cost, noise_loss) / denominator)
    )

models = {
    "linear_steps": steps.astype(float),
    "two_qubit_gates": gate_counts,
    "sqrt_gate_count": np.sqrt(gate_counts),
    "quadratic_steps": steps.astype(float) ** 2,
}

scales = sorted({
    float(r["noise_scale"]) for r in holdout
})

results = []

for model_name, cost in models.items():
    alpha = fit_coefficient(cost)

    for scale in scales:
        predicted_errors = (
            ideal_error + alpha * scale * cost
        )

        predicted_n = int(
            steps[np.argmin(predicted_errors)]
        )

        actual_rows = [
            r for r in holdout
            if float(r["noise_scale"]) == scale
        ]

        best = max(
            actual_rows,
            key=lambda r: (
                float(r["fidelity"]),
                -int(r["steps"])
            )
        )

        predicted_row = next(
            r for r in actual_rows
            if int(r["steps"]) == predicted_n
        )

        regret = (
            float(best["fidelity"])
            - float(predicted_row["fidelity"])
        )

        results.append({
            "model": model_name,
            "noise_scale": scale,
            "predicted_steps": predicted_n,
            "actual_optimal_steps": int(best["steps"]),
            "fidelity_regret": regret,
            "exact_match": int(
                predicted_n == int(best["steps"])
            ),
            "alpha": alpha,
        })

output = TABLES / "advisor_model_comparison.csv"

with output.open("w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=list(results[0].keys())
    )
    writer.writeheader()
    writer.writerows(results)

print("Q-OPTIMA MODEL COMPARISON")
print("=" * 65)

for model in models:
    subset = [
        r for r in results if r["model"] == model
    ]

    matches = sum(r["exact_match"] for r in subset)
    mean_regret = np.mean([
        r["fidelity_regret"] for r in subset
    ])

    print(
        f"{model:20s} | "
        f"Matches: {matches}/5 | "
        f"Mean regret: {mean_regret:.6f}"
    )

print()
print("Saved:", output)
