
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

STEPS = 7
SHOTS = 4096
TRIALS = 20
SCALES = np.array([1.0, 1.5, 2.0, 2.5])

processor = load_processor(
    str(ROOT / "processors" / "processor_D.json")
)

qc = trotter_circuit(
    n=4, J=1.0, g=1.0, t=2.0,
    steps=STEPS, order=1, zz_mode="cx",
    initial_label="1010", periodic=True,
)

ops = observable_ops(4)

H = tfim_hamiltonian(4, J=1.0, g=1.0, periodic=True)
initial = Statevector.from_label("1010")
exact = exact_evolution(H, initial, [2.0])[0]

ms_exact = expectations(exact, ops)["ms"]
ms_trotter = expectations(
    Statevector.from_instruction(qc), ops
)["ms"]

# Add measurements and transpile once using official settings.
measured_qc = qc.copy()
cr = ClassicalRegister(4, "m")
measured_qc.add_register(cr)
measured_qc.measure(range(4), cr)
compiled = transpile_for(measured_qc, processor)

# Create one simulator per noise scale.
simulators = [
    AerSimulator(
        noise_model=official_noise_model(scale=float(scale)),
        method="density_matrix",
    )
    for scale in SCALES
]

rows = []

print("=== Q-OPTIMA INDEPENDENT-SEED ZNE VALIDATION ===")
print(f"Processor: D | Steps: {STEPS}")
print(f"Exact Ms:         {ms_exact:.6f}")
print(f"Ideal Trotter Ms: {ms_trotter:.6f}")

for trial in range(TRIALS):
    values = []
    ses = []

    for i, simulator in enumerate(simulators):
        seed = 10000 + trial * 100 + i

        counts = simulator.run(
            compiled,
            shots=SHOTS,
            seed_simulator=seed,
        ).result().get_counts()

        result = z_observables_from_counts(counts, 4)
        values.append(result["ms"])
        ses.append(result["ms_se"])

    values = np.array(values)
    ses = np.array(ses)

    # Linear zero-noise extrapolation.
    slope, intercept = np.polyfit(SCALES, values, 1)
    zne = float(intercept)
    raw = float(values[0])

    # Propagate independent sampling standard errors
    # through the linear least-squares intercept.
    design = np.column_stack([SCALES, np.ones(len(SCALES))])
    intercept_weights = np.linalg.pinv(design)[1]
    zne_se = float(np.sqrt(np.sum(
        (intercept_weights * ses) ** 2
    )))

    rows.append({
        "trial": trial + 1,
        "shots_per_scale": SHOTS,
        "raw_ms": raw,
        "raw_se": float(ses[0]),
        "zne_ms": zne,
        "zne_se": zne_se,
        "ideal_trotter_ms": ms_trotter,
        "exact_ms": ms_exact,
        "raw_error_trotter": abs(raw - ms_trotter),
        "zne_error_trotter": abs(zne - ms_trotter),
        "raw_error_exact": abs(raw - ms_exact),
        "zne_error_exact": abs(zne - ms_exact),
        "improved": int(abs(zne - ms_trotter) < abs(raw - ms_trotter)),
    })

    print(
        f"Trial {trial + 1:02d} | "
        f"Raw={raw:+.5f} | ZNE={zne:+.5f} | "
        f"Improved={bool(rows[-1]['improved'])}"
    )

out = ROOT / "results" / "tables"
out.mkdir(parents=True, exist_ok=True)

csv_path = out / "zne_s3_validation.csv"

with open(csv_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

raw_errors = np.array([r["raw_error_trotter"] for r in rows])
zne_errors = np.array([r["zne_error_trotter"] for r in rows])

improved = sum(r["improved"] for r in rows)
raw_mean = float(np.mean(raw_errors))
zne_mean = float(np.mean(zne_errors))
reduction = 100 * (1 - zne_mean / raw_mean) if raw_mean else 0

print("\n=== FINAL ZNE VALIDATION SUMMARY ===")
print(f"Trials:                 {TRIALS}")
print(f"Improved trials:        {improved}/{TRIALS}")
print(f"Mean raw error:         {raw_mean:.6f}")
print(f"Mean ZNE error:         {zne_mean:.6f}")
print(f"Mean error reduction:   {reduction:.2f}%")
print(f"Saved: {csv_path}")

if zne_mean < raw_mean:
    print("PASS: ZNE reduced mean observable error.")
else:
    print("ZNE did not reduce mean observable error.")
