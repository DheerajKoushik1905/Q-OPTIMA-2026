
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TABLES = ROOT / "results" / "tables"

def load_csv(filename):
    with (TABLES / filename).open(
        newline="", encoding="utf-8-sig"
    ) as file:
        return list(csv.DictReader(file))

scan = load_csv("s3_scan.csv")
resources = load_csv("resources.csv")

# Match circuit resources to processor and Trotter steps.
resource_lookup = {}

for row in resources:
    if row["ps"] != "S3":
        continue

    label = row["circuit_label"]
    if not label.startswith("trotter_n"):
        continue

    steps = int(label.removeprefix("trotter_n"))
    key = (row["processor"], steps)

    resource_lookup[key] = row

candidates = []

# Fair processor comparison: same noise scale (1x).
for row in scan:
    if float(row["noise_scale"]) != 1.0:
        continue

    processor = row["processor"]
    steps = int(row["steps"])

    resource = resource_lookup.get((processor, steps))

    if resource is None:
        continue

    if resource["executable"].lower() != "true":
        continue

    candidates.append({
        "processor": processor,
        "steps": steps,
        "fidelity": float(row["fidelity_noisy"]),
        "two_q": int(resource["two_q"]),
        "depth": int(resource["depth"]),
        "physical_qubits": int(resource["physical_qubits"]),
        "routing_overhead": int(
            resource["routing_overhead_2q"]
        ),
    })

if not candidates:
    raise RuntimeError("No valid processor candidates found.")

# Highest simulated fidelity is the primary objective.
# Resource counts break ties, rather than replacing fidelity.
candidates.sort(
    key=lambda x: (
        -x["fidelity"],
        x["two_q"],
        x["depth"],
        x["physical_qubits"],
        x["processor"],
        x["steps"],
    )
)

print("\nQ-OPTIMA ULTIMATE — PROCESSOR ADVISOR")
print("=" * 55)

print("\nBEST CONFIGURATION:")
best = candidates[0]

for key, value in best.items():
    print(f"{key}: {value}")

print("\nBEST CONFIGURATION PER PROCESSOR:")
for processor in ["A", "B", "D"]:
    options = [
        row for row in candidates
        if row["processor"] == processor
    ]

    if not options:
        continue

    selected = options[0]

    print(
        f"Processor {processor}: "
        f"steps={selected['steps']}, "
        f"fidelity={selected['fidelity']:.6f}, "
        f"two_q={selected['two_q']}, "
        f"depth={selected['depth']}, "
        f"routing_overhead={selected['routing_overhead']}"
    )

# Save the ranked configurations.
output = TABLES / "ultimate_processor_ranking.csv"

with output.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "processor",
            "steps",
            "fidelity",
            "two_q",
            "depth",
            "physical_qubits",
            "routing_overhead",
        ],
    )
    writer.writeheader()
    writer.writerows(candidates)

print(f"\nSaved: {output}")
print(f"Evaluated configurations: {len(candidates)}")
