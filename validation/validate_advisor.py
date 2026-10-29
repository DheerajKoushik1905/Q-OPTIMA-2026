
import csv
import sys
from pathlib import Path

import numpy as np
from qiskit.quantum_info import Statevector

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "starter"))


from qff_sim import (
    load_processor,
    tfim_hamiltonian,
    exact_evolution,
    trotter_circuit,
    noisy_state_fidelity,
)

TABLES = ROOT / "results" / "tables"
TABLES.mkdir(parents=True, exist_ok=True)

STEPS = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16]
TEST_SCALES = [0.25, 0.75, 1.5, 2.5, 3.0]

# Read the original benchmark.
with (TABLES / "s3_scan.csv").open(newline="") as f:
    original = list(csv.DictReader(f))

training = [
    r for r in original
    if r["processor"] == "D"
    and float(r["noise_scale"]) == 1.0
]

assert len(training) == len(STEPS)

# Learn alpha ONLY from original 1x data.
n_values = np.array(
    [int(r["steps"]) for r in training],
    dtype=float
)

losses = np.array([
    float(r["fidelity_trotter_ideal"])
    - float(r["fidelity_noisy"])
    for r in training
])

alpha = float(
    np.dot(n_values, losses)
    / np.dot(n_values, n_values)
)

ideal_error = {
    int(r["steps"]):
        1.0 - float(r["fidelity_trotter_ideal"])
    for r in training
}

# Predict all five optima BEFORE running new simulations.
predictions = {}

for scale in TEST_SCALES:
    predictions[scale] = min(
        STEPS,
        key=lambda n: ideal_error[n] + alpha * scale * n
    )

print("PRE-REGISTERED ADVISOR PREDICTIONS")
print("----------------------------------")

for scale, n in predictions.items():
    print(f"Noise {scale}x -> predicted steps = {n}")

print()
print("Beginning independent simulator evaluation...")
print()

processor = load_processor(
    str(ROOT / "processors" / "processor_D.json")
)

H = tfim_hamiltonian(
    4, J=1.0, g=1.0, periodic=True
)

initial = Statevector.from_label("1010")
exact = exact_evolution(H, initial, [2.0])[0]

results = []

for scale in TEST_SCALES:
    for n in STEPS:
        qc = trotter_circuit(
            n=4,
            J=1.0,
            g=1.0,
            t=2.0,
            steps=n,
            order=1,
            zz_mode="cx",
            initial_label="1010",
            periodic=True,
        )

        fidelity = noisy_state_fidelity(
            qc,
            exact,
            processor,
            scale=scale,
            noisy=True,
        )

        results.append({
            "noise_scale": scale,
            "steps": n,
            "fidelity": fidelity,
        })

        print(
            f"Noise {scale}x | "
            f"n={n:2d} | "
            f"F={fidelity:.6f}",
            flush=True
        )

# Evaluate predictions after collecting results.
summary = []

for scale in TEST_SCALES:
    candidates = [
        r for r in results
        if r["noise_scale"] == scale
    ]

    best = max(
        candidates,
        key=lambda r: (
            r["fidelity"],
            -r["steps"]
        )
    )

    predicted_n = predictions[scale]

    predicted_result = next(
        r for r in candidates
        if r["steps"] == predicted_n
    )

    regret = (
        best["fidelity"]
        - predicted_result["fidelity"]
    )

    summary.append({
        "noise_scale": scale,
        "predicted_steps": predicted_n,
        "actual_optimal_steps": best["steps"],
        "fidelity_at_prediction": predicted_result["fidelity"],
        "optimal_fidelity": best["fidelity"],
        "fidelity_regret": regret,
        "exact_match": predicted_n == best["steps"],
    })

with (TABLES / "advisor_holdout_scan.csv").open(
    "w", newline=""
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "noise_scale", "steps", "fidelity"
        ]
    )
    writer.writeheader()
    writer.writerows(results)

with (TABLES / "advisor_holdout_summary.csv").open(
    "w", newline=""
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=list(summary[0].keys())
    )
    writer.writeheader()
    writer.writerows(summary)

print()
print("=" * 65)
print("INDEPENDENT VALIDATION RESULTS")
print("=" * 65)

matches = 0

for row in summary:
    matches += int(row["exact_match"])

    print(
        f"Noise {row['noise_scale']}x | "
        f"Predicted n={row['predicted_steps']} | "
        f"Actual n*={row['actual_optimal_steps']} | "
        f"Regret={row['fidelity_regret']:.6f} | "
        f"Match={row['exact_match']}"
    )

print()
print(f"Exact matches: {matches}/{len(summary)}")
print(
    "Mean fidelity regret:",
    f"{np.mean([r['fidelity_regret'] for r in summary]):.6f}"
)
print("PASS: Holdout evaluation completed")
