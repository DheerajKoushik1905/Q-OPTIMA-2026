
import sys
from pathlib import Path

from qiskit.quantum_info import Statevector

# Import the official organizer helper.
sys.path.insert(0, str(Path(__file__).parent / "starter"))

from qff_sim import (
    load_processor,
    tfim_hamiltonian,
    exact_evolution,
    trotter_circuit,
    noisy_state_fidelity,
)

print("=== PHASE 2: NOISY FIDELITY TEST ===", flush=True)

# Our official PS-S3 problem settings.
N = 4
J = 1.0
G = 1.0
T = 2.0
INITIAL_STATE = "1010"

# Load our validated custom processor.
processor_d = load_processor("processors/processor_D.json")

# Calculate the exact quantum state.
H = tfim_hamiltonian(N, J=J, g=G, periodic=True)
initial = Statevector.from_label(INITIAL_STATE)
exact = exact_evolution(H, initial, [T])[0]

print("Processor: D (four-qubit ring)", flush=True)
print("Initial state: |1010>", flush=True)
print("Time: 2.0", flush=True)
print()
print("Steps | Ideal Fidelity | Noisy Fidelity", flush=True)
print("----------------------------------------", flush=True)

for steps in [1, 4, 8]:
    # Use the official first-order Trotter circuit.
    qc = trotter_circuit(
        n=N,
        J=J,
        g=G,
        t=T,
        steps=steps,
        order=1,
        zz_mode="cx",
        initial_label=INITIAL_STATE,
        periodic=True,
    )

    ideal_fidelity = noisy_state_fidelity(
        qc, exact, processor_d, scale=1.0, noisy=False
    )

    noisy_fidelity = noisy_state_fidelity(
        qc, exact, processor_d, scale=1.0, noisy=True
    )

    print(
        f"{steps:5d} | {ideal_fidelity:14.8f} | "
        f"{noisy_fidelity:14.8f}",
        flush=True,
    )

print()
print("PASS: First noisy fidelity test completed.", flush=True)
