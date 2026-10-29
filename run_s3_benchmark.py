
import csv
import sys
from pathlib import Path

from qiskit.quantum_info import Statevector

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "starter"))

from qff_sim import (
    PROCESSOR_A,
    PROCESSOR_B,
    load_processor,
    tfim_hamiltonian,
    observable_ops,
    exact_evolution,
    expectations,
    trotter_circuit,
    noisy_state_fidelity,
    run_z_measurement,
    circuit_metrics,
)

STEPS = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16]
SHOTS = 4096

OUT = ROOT / "results" / "tables"
OUT.mkdir(parents=True, exist_ok=True)

processors = {
    "A": (PROCESSOR_A, [1.0]),
    "B": (PROCESSOR_B, [1.0]),
    "D": (
        load_processor(str(ROOT / "processors" / "processor_D.json")),
        [0.5, 1.0, 2.0],
    ),
}

H = tfim_hamiltonian(4, J=1.0, g=1.0, periodic=True)
initial = Statevector.from_label("1010")
exact = exact_evolution(H, initial, [2.0])[0]
ms_exact = expectations(exact, observable_ops(4))["ms"]

scan_fields = [
    "processor", "noise_scale", "steps",
    "fidelity_noisy", "fidelity_trotter_ideal",
    "ms_noisy", "ms_noisy_se", "ms_exact",
    "logical_2q", "swap_2q", "two_q",
]

resource_fields = [
    "ps", "circuit_label", "processor", "executable",
    "logical_qubits", "physical_qubits", "logical_2q",
    "two_q", "depth", "two_q_depth", "swaps",
    "routing_overhead_2q",
]

scan_rows = []
resource_rows = []

for name, (processor, scales) in processors.items():
    print(f"\n=== Processor {name} ===", flush=True)

    for steps in STEPS:
        qc = trotter_circuit(
            n=4, J=1.0, g=1.0, t=2.0,
            steps=steps, order=1,
            zz_mode="cx",
            initial_label="1010",
            periodic=True,
        )

        metrics = circuit_metrics(qc, processor)

        resource_rows.append({
            "ps": "S3",
            "circuit_label": f"trotter_n{steps}",
            "processor": name,
            "executable": metrics["executable"],
            "logical_qubits": metrics["logical_qubits"],
            "physical_qubits": metrics["physical_qubits"],
            "logical_2q": metrics["logical_cx"],
            "two_q": metrics["cx"],
            "depth": metrics["depth"],
            "two_q_depth": metrics["two_q_depth"],
            "swaps": metrics["swaps"],
            "routing_overhead_2q": metrics["cx_overhead"],
        })

        ideal_fidelity = noisy_state_fidelity(
            qc, exact, processor, noisy=False
        )

        for scale in scales:
            noisy_fidelity = noisy_state_fidelity(
                qc, exact, processor,
                scale=scale, noisy=True
            )

            measured = run_z_measurement(
                qc, processor, shots=SHOTS,
                noisy=True, scale=scale
            )

            scan_rows.append({
                "processor": name,
                "noise_scale": scale,
                "steps": steps,
                "fidelity_noisy": noisy_fidelity,
                "fidelity_trotter_ideal": ideal_fidelity,
                "ms_noisy": measured["ms"],
                "ms_noisy_se": measured["ms_se"],
                "ms_exact": ms_exact,
                "logical_2q": metrics["logical_cx"],
                "swap_2q": metrics["cx_overhead"],
                "two_q": metrics["cx"],
            })

            print(
                f"{name} | scale={scale} | "
                f"steps={steps:2d} | "
                f"noisy fidelity={noisy_fidelity:.6f}",
                flush=True,
            )

            # Save partial progress after every experiment.
            with open(OUT / "s3_scan.csv", "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=scan_fields)
                writer.writeheader()
                writer.writerows(scan_rows)

    with open(OUT / "resources.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=resource_fields)
        writer.writeheader()
        writer.writerows(resource_rows)

summary_rows = []

for name, (_, scales) in processors.items():
    for scale in scales:
        candidates = [
            row for row in scan_rows
            if row["processor"] == name
            and row["noise_scale"] == scale
        ]

        best = max(
            candidates,
            key=lambda row: (
                row["fidelity_noisy"],
                -row["steps"],
            ),
        )

        summary_rows.append({
            "processor": name,
            "noise_scale": scale,
            "n_star": best["steps"],
            "fidelity_at_n_star": best["fidelity_noisy"],
        })

with open(OUT / "s3_summary.csv", "w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "processor", "noise_scale",
            "n_star", "fidelity_at_n_star",
        ],
    )
    writer.writeheader()
    writer.writerows(summary_rows)

print("\n=== OPTIMAL TROTTER STEPS ===")
for row in summary_rows:
    print(row)

print("\nPASS: 60 noisy experiments completed.")
print("Saved results/tables/s3_scan.csv")
print("Saved results/tables/s3_summary.csv")
print("Saved results/tables/resources.csv")
