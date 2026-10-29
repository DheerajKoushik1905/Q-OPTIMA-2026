
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TABLES = ROOT / "results" / "tables"

STEPS = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16]

def read_csv(filename):
    with (TABLES / filename).open(
        newline="", encoding="utf-8-sig"
    ) as f:
        return list(csv.DictReader(f))

scan = read_csv("s3_scan.csv")
resources = read_csv("resources.csv")

# Train V2's quadratic penalty on Processor D at 1x noise.
training = [
    row for row in scan
    if row["processor"] == "D"
    and float(row["noise_scale"]) == 1.0
]

if len(training) != len(STEPS):
    raise RuntimeError("Expected 12 Processor D training rows.")

ideal_error = {
    int(row["steps"]):
        1.0 - float(row["fidelity_trotter_ideal"])
    for row in training
}

numerator = 0.0
denominator = 0.0

for row in training:
    n = int(row["steps"])
    observed_penalty = (
        float(row["fidelity_trotter_ideal"])
        - float(row["fidelity_noisy"])
    )
    numerator += n**2 * observed_penalty
    denominator += n**4

alpha = max(0.0, numerator / denominator)

resource_lookup = {}

for row in resources:
    if row["ps"] != "S3":
        continue

    label = row["circuit_label"]
    if not label.startswith("trotter_n"):
        continue

    n = int(label.removeprefix("trotter_n"))
    resource_lookup[(row["processor"], n)] = row

def recommend(scale):
    # Step count predicted using V2 quadratic model.
    predicted_step = min(
        STEPS,
        key=lambda n: (
            ideal_error[n] + alpha * scale * n**2,
            n,
        )
    )

    # Processor selection based on measured circuit resources.
    candidates = []

    for processor in ["A", "B", "D"]:
        row = resource_lookup.get((processor, predicted_step))

        if row is None:
            continue

        if row["executable"].lower() != "true":
            continue

        candidates.append({
            "processor": processor,
            "steps": predicted_step,
            "two_q": int(row["two_q"]),
            "depth": int(row["depth"]),
            "physical_qubits": int(row["physical_qubits"]),
            "routing_overhead": int(
                row["routing_overhead_2q"]
            ),
        })

    # Resource-based selection; no unmeasured fidelity claims.
    candidates.sort(
        key=lambda x: (
            x["two_q"],
            x["depth"],
            x["physical_qubits"],
            x["processor"],
        )
    )

    return candidates[0], candidates

scales = [0.4, 0.5, 0.9, 1.0, 1.25, 1.8, 2.0, 2.8]

output_rows = []

print("\nQ-OPTIMA ULTIMATE — HYBRID ADVISOR")
print("=" * 55)
print(f"Quadratic coefficient: {alpha:.8f}")

for scale in scales:
    best, candidates = recommend(scale)

    print(
        f"Noise {scale:.2f}x | "
        f"Processor {best['processor']} | "
        f"Steps {best['steps']} | "
        f"Two-qubit gates {best['two_q']} | "
        f"Physical qubits {best['physical_qubits']}"
    )

    output_rows.append({
        "noise_scale": scale,
        **best,
    })

output = TABLES / "ultimate_hybrid_recommendations.csv"

with output.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f, fieldnames=list(output_rows[0].keys())
    )
    writer.writeheader()
    writer.writerows(output_rows)

print(f"\nSaved: {output}")
