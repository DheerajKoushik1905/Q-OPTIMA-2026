
import csv
import sys
from pathlib import Path
from statistics import mean

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
SCALES = [0.4, 0.9, 1.25, 1.8, 2.8]
FIXED_STEPS = [6, 7, 8, 16]

with (TABLES / "advisor_final_validation.csv").open(
    newline=""
) as f:
    advisor = list(csv.DictReader(f))

processor = load_processor(
    str(ROOT / "processors" / "processor_D.json")
)

H = tfim_hamiltonian(
    4, J=1.0, g=1.0, periodic=True
)

initial = Statevector.from_label("1010")
exact = exact_evolution(H, initial, [2.0])[0]

# Reproduce the complete fidelity scan.
scan = []

for scale in SCALES:
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

        scan.append({
            "noise_scale": scale,
            "steps": n,
            "fidelity": fidelity,
        })

        print(
            f"Noise {scale}x | "
            f"n={n:2d} | "
            f"F={fidelity:.6f}",
            flush=True,
        )

# Save the complete scan for reproducibility.
scan_path = TABLES / "v2_fixed_step_scan.csv"

with scan_path.open("w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["noise_scale", "steps", "fidelity"]
    )
    writer.writeheader()
    writer.writerows(scan)

strategies = (
    ["linear", "quadratic"]
    + [f"fixed_{n}" for n in FIXED_STEPS]
)

comparison = []

for scale in SCALES:
    candidates = [
        r for r in scan
        if r["noise_scale"] == scale
    ]

    best = max(
        candidates,
        key=lambda r: (
            r["fidelity"],
            -r["steps"]
        )
    )

    for strategy in strategies:
        if strategy.startswith("fixed_"):
            chosen_n = int(strategy.split("_")[1])
        else:
            matching = next(
                r for r in advisor
                if r["model"] == strategy
                and float(r["noise_scale"]) == scale
            )
            chosen_n = int(matching["predicted_steps"])

        chosen = next(
            r for r in candidates
            if r["steps"] == chosen_n
        )

        comparison.append({
            "noise_scale": scale,
            "strategy": strategy,
            "chosen_steps": chosen_n,
            "optimal_steps": best["steps"],
            "chosen_fidelity": chosen["fidelity"],
            "optimal_fidelity": best["fidelity"],
            "fidelity_regret": (
                best["fidelity"] - chosen["fidelity"]
            ),
            "exact_match": int(
                chosen_n == best["steps"]
            ),
        })

output = TABLES / "v2_fixed_step_comparison.csv"

with output.open("w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=list(comparison[0].keys())
    )
    writer.writeheader()
    writer.writerows(comparison)

print()
print("Q-OPTIMA V2 — FIXED-STEP BASELINE COMPARISON")
print("=" * 75)

for strategy in strategies:
    rows = [
        r for r in comparison
        if r["strategy"] == strategy
    ]

    matches = sum(r["exact_match"] for r in rows)
    regret = mean(
        r["fidelity_regret"] for r in rows
    )

    print(
        f"{strategy:12s} | "
        f"Matches: {matches}/5 | "
        f"Mean regret: {regret:.6f}"
    )

print()
print("Saved:", scan_path)
print("Saved:", output)
print("PASS: Fixed-step comparison completed")
