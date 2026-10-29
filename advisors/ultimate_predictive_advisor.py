
import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "results" / "tables"

STEPS = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16]

def read_csv(name):
    with (TABLES / name).open(
        newline="", encoding="utf-8-sig"
    ) as f:
        return list(csv.DictReader(f))

scan = read_csv("s3_scan.csv")
resources = read_csv("resources.csv")

# Build processor/step resource lookup.
resource_lookup = {}

for r in resources:
    if r["ps"] != "S3":
        continue

    if not r["circuit_label"].startswith("trotter_n"):
        continue

    n = int(r["circuit_label"].replace("trotter_n", ""))

    resource_lookup[(r["processor"], n)] = {
        "two_q": float(r["two_q"]),
        "depth": float(r["depth"]),
        "physical_qubits": int(r["physical_qubits"]),
        "routing_overhead": float(
            r["routing_overhead_2q"]
        ),
    }

# Train only on 1x noise.
training = [
    r for r in scan
    if float(r["noise_scale"]) == 1.0
]

# Ideal approximation error is known from the
# noise-free Trotter simulation.
ideal_error = {
    int(r["steps"]): 1.0 - float(
        r["fidelity_trotter_ideal"]
    )
    for r in training
}

# Fit a nonnegative one-parameter resource model:
# E_hat = E_ideal + alpha * noise_scale * two_q
#
# We intentionally avoid fitting a separate
# coefficient for each processor.
numerator = 0.0
denominator = 0.0

for r in training:
    p = r["processor"]
    n = int(r["steps"])

    if (p, n) not in resource_lookup:
        continue

    gate_count = resource_lookup[(p, n)]["two_q"]

    observed_noise_penalty = (
        float(r["fidelity_trotter_ideal"])
        - float(r["fidelity_noisy"])
    )

    numerator += gate_count * observed_noise_penalty
    denominator += gate_count ** 2

alpha = max(0.0, numerator / denominator)

def predict_error(processor, steps, noise_scale):
    gates = resource_lookup[
        (processor, steps)
    ]["two_q"]

    return (
        ideal_error[steps]
        + alpha * noise_scale * gates
    )

def recommend(noise_scale):
    candidates = []

    for processor in ["A", "B", "D"]:
        for steps in STEPS:
            resource = resource_lookup.get(
                (processor, steps)
            )

            if resource is None:
                continue

            error = predict_error(
                processor, steps, noise_scale
            )

            candidates.append({
                "processor": processor,
                "steps": steps,
                "predicted_error": error,
                "predicted_fidelity": max(
                    0.0, min(1.0, 1.0 - error)
                ),
                "two_q": int(resource["two_q"]),
                "depth": int(resource["depth"]),
                "physical_qubits": resource[
                    "physical_qubits"
                ],
                "routing_overhead": int(
                    resource["routing_overhead"]
                ),
            })

    candidates.sort(
        key=lambda r: (
            r["predicted_error"],
            r["two_q"],
            r["depth"],
            r["physical_qubits"],
            r["processor"],
        )
    )

    return candidates[0], candidates

print("\nQ-OPTIMA ULTIMATE — PREDICTIVE ADVISOR")
print("=" * 55)
print(f"Fitted gate-noise coefficient: {alpha:.8f}")

scales = [0.5, 1.0, 2.0, 0.4, 0.9, 1.25, 1.8, 2.8]

all_rows = []

for scale in scales:
    best, ranked = recommend(scale)

    print(
        f"Noise {scale:>4.2f}x | "
        f"Processor {best['processor']} | "
        f"steps={best['steps']:>2} | "
        f"predicted fidelity="
        f"{best['predicted_fidelity']:.6f}"
    )

    for r in ranked:
        all_rows.append({
            "noise_scale": scale,
            **r,
        })

output = TABLES / "ultimate_predictions.csv"

with output.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "noise_scale",
            "processor",
            "steps",
            "predicted_error",
            "predicted_fidelity",
            "two_q",
            "depth",
            "physical_qubits",
            "routing_overhead",
        ],
    )

    writer.writeheader()
    writer.writerows(all_rows)

print(f"\nSaved: {output}")
print(f"Total predictions: {len(all_rows)}")
