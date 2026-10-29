
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
STEPS = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16]

# Fresh evaluation settings not used in previous tests.
TEST_SCALES = [0.4, 0.9, 1.25, 1.8, 2.8]

with (TABLES / "s3_scan.csv").open(newline="") as f:
    original = list(csv.DictReader(f))

training = sorted(
    [
        r for r in original
        if r["processor"] == "D"
        and float(r["noise_scale"]) == 1.0
    ],
    key=lambda r: int(r["steps"])
)

assert len(training) == len(STEPS)

steps = np.array(
    [int(r["steps"]) for r in training],
    dtype=float
)

ideal_error = np.array([
    1.0 - float(r["fidelity_trotter_ideal"])
    for r in training
])

noise_loss = np.array([
    float(r["fidelity_trotter_ideal"])
    - float(r["fidelity_noisy"])
    for r in training
])

# Freeze both model coefficients using original training data.
linear_cost = steps
quadratic_cost = steps ** 2

alpha_linear = max(
    0.0,
    float(np.dot(linear_cost, noise_loss)
          / np.dot(linear_cost, linear_cost))
)

alpha_quadratic = max(
    0.0,
    float(np.dot(quadratic_cost, noise_loss)
          / np.dot(quadratic_cost, quadratic_cost))
)

# Predictions are calculated BEFORE the new simulations.
predictions = {}

for scale in TEST_SCALES:
    linear_n = int(steps[np.argmin(
        ideal_error + alpha_linear * scale * linear_cost
    )])

    quadratic_n = int(steps[np.argmin(
        ideal_error + alpha_quadratic * scale * quadratic_cost
    )])

    predictions[scale] = {
        "linear": linear_n,
        "quadratic": quadratic_n,
    }

print("FROZEN MODEL PREDICTIONS")
print("=" * 60)

for scale, prediction in predictions.items():
    print(
        f"Noise {scale}x | "
        f"Linear n={prediction['linear']} | "
        f"Quadratic n={prediction['quadratic']}"
    )

processor = load_processor(
    str(ROOT / "processors" / "processor_D.json")
)

H = tfim_hamiltonian(4, J=1.0, g=1.0, periodic=True)
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
            f"Noise {scale}x | n={n:2d} | "
            f"F={fidelity:.6f}",
            flush=True
        )

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

    for model in ["linear", "quadratic"]:
        predicted_n = predictions[scale][model]

        predicted_result = next(
            r for r in candidates
            if r["steps"] == predicted_n
        )

        summary.append({
            "model": model,
            "noise_scale": scale,
            "predicted_steps": predicted_n,
            "actual_optimal_steps": best["steps"],
            "fidelity_regret": (
                best["fidelity"]
                - predicted_result["fidelity"]
            ),
            "exact_match": int(
                predicted_n == best["steps"]
            ),
        })

output = TABLES / "advisor_final_validation.csv"

with output.open("w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=list(summary[0].keys())
    )
    writer.writeheader()
    writer.writerows(summary)

print()
print("FINAL ADVISOR VALIDATION")
print("=" * 60)

for model in ["linear", "quadratic"]:
    subset = [
        r for r in summary
        if r["model"] == model
    ]

    matches = sum(r["exact_match"] for r in subset)
    mean_regret = np.mean([
        r["fidelity_regret"] for r in subset
    ])

    print(
        f"{model:12s} | "
        f"Matches: {matches}/5 | "
        f"Mean regret: {mean_regret:.6f}"
    )

print()
print("Saved:", output)
print("PASS: Fresh advisor validation completed")
