
import csv
from pathlib import Path
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
TABLE = ROOT / "results" / "tables" / "s3_scan.csv"
FIGURES = ROOT / "results" / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

with TABLE.open(newline="") as f:
    rows = list(csv.DictReader(f))

for row in rows:
    row["steps"] = int(row["steps"])
    row["noise_scale"] = float(row["noise_scale"])
    row["fidelity_noisy"] = float(row["fidelity_noisy"])
    row["fidelity_trotter_ideal"] = float(
        row["fidelity_trotter_ideal"]
    )

def series(processor, scale):
    return sorted(
        [
            r for r in rows
            if r["processor"] == processor
            and r["noise_scale"] == scale
        ],
        key=lambda r: r["steps"],
    )

# Graph 1: Compare the three processors at 1x noise.
plt.figure(figsize=(9, 5))

for processor in ["A", "B", "D"]:
    data = series(processor, 1.0)
    plt.plot(
        [r["steps"] for r in data],
        [r["fidelity_noisy"] for r in data],
        marker="o",
        label=f"Processor {processor}",
    )

plt.xlabel("Trotter steps")
plt.ylabel("Noisy state fidelity")
plt.title("PS-S3: Processor comparison at 1x noise")
plt.ylim(0, 1)
plt.grid(alpha=0.25)
plt.legend()
plt.tight_layout()
plt.savefig(FIGURES / "processor_comparison.png", dpi=200)
plt.close()

# Graph 2: Show how noise changes Processor D's optimum.
plt.figure(figsize=(9, 5))

data = series("D", 1.0)
plt.plot(
    [r["steps"] for r in data],
    [r["fidelity_trotter_ideal"] for r in data],
    "k--",
    label="Ideal Trotter fidelity",
)

for scale in [0.5, 1.0, 2.0]:
    data = series("D", scale)
    xs = [r["steps"] for r in data]
    ys = [r["fidelity_noisy"] for r in data]
    plt.plot(xs, ys, marker="o", label=f"Noise {scale}x")

    best = max(data, key=lambda r: r["fidelity_noisy"])
    plt.annotate(
        f"n*={best['steps']}",
        (best["steps"], best["fidelity_noisy"]),
        xytext=(5, 8),
        textcoords="offset points",
        fontsize=9,
    )

plt.xlabel("Trotter steps")
plt.ylabel("State fidelity")
plt.title("PS-S3: Noise accumulation and optimal steps")
plt.ylim(0, 1.05)
plt.grid(alpha=0.25)
plt.legend()
plt.tight_layout()
plt.savefig(FIGURES / "noise_crossover.png", dpi=200)
plt.close()

print("PASS: Both graphs created.")
print(FIGURES / "processor_comparison.png")
print(FIGURES / "noise_crossover.png")
