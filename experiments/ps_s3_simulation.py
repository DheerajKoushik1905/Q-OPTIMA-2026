
import numpy as np
from scipy.linalg import expm
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, state_fidelity

# Official PS-S3 parameters
N = 4
J = 1.0
G = 1.0
T = 2.0

STEPS = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16]

# Four-qubit ring, even bonds followed by odd bonds
EVEN_BONDS = [(0, 1), (2, 3)]
ODD_BONDS = [(1, 2), (3, 0)]


def build_hamiltonian():
    """Construct the exact four-qubit TFIM ring Hamiltonian."""
    I = np.eye(2, dtype=complex)
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)

    def pauli_term(operators):
        result = np.array([[1]], dtype=complex)
        for op in reversed(operators):
            result = np.kron(result, op)
        return result

    H = np.zeros((2**N, 2**N), dtype=complex)

    for a, b in EVEN_BONDS + ODD_BONDS:
        ops = [I] * N
        ops[a] = Z
        ops[b] = Z
        H -= J * pauli_term(ops)

    for q in range(N):
        ops = [I] * N
        ops[q] = X
        H -= G * pauli_term(ops)

    return H


def initial_circuit():
    """Prepare the Neel state |1010>."""
    qc = QuantumCircuit(N)
    qc.x(1)
    qc.x(3)
    return qc


def trotter_circuit(steps):
    """First-order Trotter evolution with prescribed bond ordering."""
    qc = initial_circuit()
    dt = T / steps

    for _ in range(steps):
        for a, b in EVEN_BONDS:
            qc.rzz(-2 * J * dt, a, b)

        for a, b in ODD_BONDS:
            qc.rzz(-2 * J * dt, a, b)

        for q in range(N):
            qc.rx(-2 * G * dt, q)

    return qc


def staggered_magnetization(state):
    """M_s = (Z0 - Z1 + Z2 - Z3) / 4."""
    probabilities = np.abs(state.data) ** 2
    total = 0.0

    for basis_state, probability in enumerate(probabilities):
        magnetization = 0.0

        for q in range(N):
            bit = (basis_state >> q) & 1
            z = 1 if bit == 0 else -1
            magnetization += ((-1) ** q) * z

        total += probability * magnetization / N

    return float(total)


def main():
    H = build_hamiltonian()

    initial = Statevector.from_instruction(initial_circuit())
    exact_vector = expm(-1j * H * T) @ initial.data
    exact = Statevector(exact_vector)

    print("=== QFF 2026 PHASE 2: PS-S3 ===")
    print("Initial state: |1010>")
    print("Evolution time:", T)
    print("Exact staggered magnetization:",
          round(staggered_magnetization(exact), 6))

    print("\nSteps | Ideal fidelity | Ideal M_s")
    print("-" * 43)

    for steps in STEPS:
        circuit = trotter_circuit(steps)
        approximate = Statevector.from_instruction(circuit)

        fidelity = state_fidelity(exact, approximate)
        ms = staggered_magnetization(approximate)

        print(f"{steps:5d} | {fidelity:14.8f} | {ms:10.6f}")

    print("\nPASS: Ideal Trotter scan completed.")


if __name__ == "__main__":
    main()
