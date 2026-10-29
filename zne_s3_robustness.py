
import csv
import sys
from pathlib import Path

import numpy as np
from qiskit import ClassicalRegister
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "starter"))

from qff_sim import (
    load_processor,
    tfim_hamiltonian,
    observable_ops,
    exact_evolution,
    expectations,
    trotter_circuit,
    transpile_for,
    official_noise_model,
    z_observables_from_counts,
)

STEP_COUNTS = [6, 7, 8]
SCALES = np.array([1.0, 1.5, 2.0, 2.5])
SHOTS = 4096
TRIALS = 20

processor = load_processor(
    str(ROOT / "processors" / "processor_D.json")
)

ops = observable_ops(4)
H = tfim_hamiltonian(4, J=1.0, g=1.0, periodic=True)
initial = Statevector.from_label("1010")
exact = exact_evolution(H, initial, [2.0])[0]
ms_exact = expectations(exact, ops)["ms"]

out = ROOT / "results" / "tables"
out.mkdir(parents=True, exist_ok=True)

# Linear least-squares intercept weights.
design = np.column_stack([SCALES, np.ones(len(SCALES))])
weights = np.linalg.pinv(design)[1]

summary_rows = []
all_rows = []

for steps in STEP_COUNTS:
    qc = trotter_circuit(
        n=4, J=1.0, g=1.0, t=2.0,
        steps=steps, order=1, zz_mode="cx",
        initial_label="1010", periodic=True,
    )

    ms_trotter = expectations(
        Statevector.from_instruction(qc), ops
    )["ms"]

    measured = qc.copy()
    cr = ClassicalRegister(4, "m")
    measured.add_register(cr)
    measured.measure(range(4), cr)
    compiled = transpile_for(measured, processor)

    simulators = [
        AerSimulator(
            noise_model=official_noise_model(scale=float(scale)),
            method="density_matrix",
        )
        for scale in SCALES
    ]

    raw_errors = []
    zne_errors = []
    improved = 0

    print(f"\n=== {steps} TROTTER STEPS ===")

    for trial in range(TRIALS):
        values = []

        for i, simulator in enumerate(simulators):
            seed = 20000 + steps * 1000 + trial * 10 + i

            counts = simulator.run(
                compiled,
                shots=SHOTS,
                seed_simulator=seed,
            ).result().get_counts()

            result = z_observables_from_counts(counts, 4)
            values.append(result["ms"])

        raw = float(values[0])
        zne = float(np.dot(weights, values))

        raw_error = abs(raw - ms_trotter)
        zne_error = abs(zne - ms_trotter)

        raw_errors.append(raw_error)
        zne_errors.append(zne_error)

        success = zne_error < raw_error
        improved += int(success)

        all_rows.append({
            "steps": steps,
            "trial": trial + 1,
            "shots_per_scale": SHOTS,
            "raw_ms": raw,
            "zne_ms": zne,
            "ideal_trotter_ms": ms_trotter,
            "exact_ms": ms_exact,
            "raw_error_trotter": raw_error,
            "zne_error_trotter": zne_error,
            "improved": int(success),
        })

    mean_raw = float(np.mean(raw_errors))
    mean_zne = float(np.mean(zne_errors))
    reduction = (
        100 * (1 - mean_zne / mean_raw)
        if mean_raw > 0 else 0
    )

    summary_rows.append({
        "steps": steps,
        "improved_trials": improved,
        "total_trials": TRIALS,
        "mean_raw_error": mean_raw,
        "mean_zne_error": mean_zne,
        "error_reduction_percent": reduction,
    })

    print(f"Improved trials:      {improved}/{TRIALS}")
    print(f"Mean raw error:       {mean_raw:.6f}")
    print(f"Mean ZNE error:       {mean_zne:.6f}")
    print(f"Mean error reduction: {reduction:.2f}%")

with open(out / "zne_s3_robustness.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
    writer.writeheader()
    writer.writerows(all_rows)

with open(out / "zne_s3_robustness_summary.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=summary_rows[0].keys())
    writer.writeheader()
    writer.writerows(summary_rows)

print("\nPASS: Robustness experiment completed.")
print("Saved results/tables/zne_s3_robustness.csv")
print("Saved results/tables/zne_s3_robustness_summary.csv")
