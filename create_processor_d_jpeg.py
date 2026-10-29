
from pathlib import Path
import matplotlib.pyplot as plt

# Processor D: four-qubit ring
positions = {
    0: (0, 1),
    1: (1, 1),
    2: (1, 0),
    3: (0, 0),
}

edges = [(0, 1), (1, 2), (2, 3), (3, 0)]

fig, ax = plt.subplots(figsize=(9, 7))
fig.patch.set_facecolor("white")

# Draw connections
for a, b in edges:
    x1, y1 = positions[a]
    x2, y2 = positions[b]
    ax.plot(
        [x1, x2], [y1, y2],
        color="#2563eb",
        linewidth=5,
        zorder=1
    )

# Draw qubits
for q, (x, y) in positions.items():
    ax.scatter(
        x, y,
        s=5000,
        color="#dbeafe",
        edgecolors="#1d4ed8",
        linewidths=3,
        zorder=2
    )
    ax.text(
        x, y, f"q{q}",
        ha="center",
        va="center",
        fontsize=20,
        fontweight="bold",
        zorder=3
    )

ax.set_xlim(-0.35, 1.35)
ax.set_ylim(-0.35, 1.35)
ax.set_aspect("equal")
ax.axis("off")

fig.suptitle(
    "Processor D — Four-Qubit Ring",
    fontsize=22,
    fontweight="bold",
    y=0.97
)

fig.text(
    0.5, 0.10,
    "Connections: (0,1), (1,2), (2,3), (3,0)",
    ha="center",
    fontsize=12
)

fig.text(
    0.5, 0.06,
    "Basis gates: rz, sx, x, cx",
    ha="center",
    fontsize=11
)

output = Path("processors") / "Processor_D_3AM_ENGINEERS.jpg"
output.parent.mkdir(parents=True, exist_ok=True)

fig.savefig(
    output,
    dpi=300,
    bbox_inches="tight",
    facecolor="white"
)

plt.close(fig)

print(f"SUCCESS: JPEG created at {output.resolve()}")


