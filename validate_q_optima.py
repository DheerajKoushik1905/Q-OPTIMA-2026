
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TABLES = ROOT / "results" / "tables"

def read_csv(filename):
    with (TABLES / filename).open(newline="") as f:
        return list(csv.DictReader(f))

resources = read_csv("resources.csv")
scan = read_csv("s3_scan.csv")
summary = read_csv("s3_summary.csv")
bell = read_csv("bell.csv")

assert len(resources) == 36, "Expected 36 resource rows"
assert len(scan) == 60, "Expected 60 benchmark rows"
assert len(summary) == 5, "Expected 5 summary rows"
assert len(bell) == 4, "Expected 4 Bell rows"

for row in resources:
    logical = int(row["logical_2q"])
    physical = int(row["two_q"])
    overhead = int(row["routing_overhead_2q"])
    swaps = int(row["swaps"])

    assert logical >= 0
    assert physical >= 0
    assert swaps >= 0
    assert overhead == physical - logical, (
        f"Routing mismatch: {row}"
    )

for row in scan:
    noisy = float(row["fidelity_noisy"])
    ideal = float(row["fidelity_trotter_ideal"])

    assert -1e-9 <= noisy <= 1 + 1e-9
    assert -1e-9 <= ideal <= 1 + 1e-9

for row in summary:
    matching = [
        x for x in scan
        if x["processor"] == row["processor"]
        and float(x["noise_scale"]) == float(row["noise_scale"])
    ]

    assert matching, f"No matching scan rows: {row}"

    best = max(
        matching,
        key=lambda x: (
            float(x["fidelity_noisy"]),
            -int(x["steps"])
        )
    )

    assert int(row["n_star"]) == int(best["steps"])
    assert abs(
        float(row["fidelity_at_n_star"])
        - float(best["fidelity_noisy"])
    ) < 1e-9

for row in bell:
    fidelity = float(row["fidelity"])
    assert -0.1 <= fidelity <= 1.1

print("PASS: All required CSV row counts")
print("PASS: Routing overhead arithmetic")
print("PASS: Fidelity ranges")
print("PASS: Optimal Trotter-step summaries")
print("PASS: Bell fidelity sanity checks")
print()
print("Q-OPTIMA initial data validation completed.")
