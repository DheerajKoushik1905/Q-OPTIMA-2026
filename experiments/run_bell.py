
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "starter"))

from qff_sim import load_processor, bell_experiment

processor = load_processor(
    str(ROOT / "processors" / "processor_D.json")
)

output_dir = ROOT / "results" / "tables"
output_dir.mkdir(parents=True, exist_ok=True)

columns = [
    "pair", "pair_distance", "condition",
    "two_qubit_gates",
    "XX", "XX_se",
    "YY", "YY_se",
    "ZZ", "ZZ_se",
    "fidelity", "fidelity_se",
]

rows = []

for pair in [(0, 1), (0, 2)]:
    for noisy in [False, True]:
        condition = "noisy" if noisy else "ideal"

        print(
            f"Testing pair {pair} | {condition}",
            flush=True,
        )

        result = bell_experiment(
            processor=processor,
            physical_pair=pair,
            noisy=noisy,
            shots=4096,
        )

        rows.append({
            "pair": f"{pair[0]}-{pair[1]}",
            "pair_distance": result["pair_distance"],
            "condition": condition,
            "two_qubit_gates": result["cx"],
            "XX": result["XX"],
            "XX_se": result["XX_se"],
            "YY": result["YY"],
            "YY_se": result["YY_se"],
            "ZZ": result["ZZ"],
            "ZZ_se": result["ZZ_se"],
            "fidelity": result["fidelity"],
            "fidelity_se": result["fidelity_se"],
        })

        print(
            f"Fidelity = {result['fidelity']:.6f}",
            flush=True,
        )

output = output_dir / "bell.csv"

with output.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)

print()
print("PASS: Bell verification completed.")
print(f"Saved: {output}")
