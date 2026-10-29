# Q-OPTIMA 2026
### Noise-Aware Trotter-Step Optimization for Quantum Simulation

**Qiskit Fall Fest 2026 | Phase 2 | Quantum Simulation | PS-S3**

## Overview

Q-OPTIMA investigates how Trotter approximation error, quantum gate noise, and processor connectivity influence the accuracy of digital quantum simulation.

Its central contribution is a noise-aware advisor that recommends a Trotter step count instead of blindly increasing circuit depth.

## Research Question

**Can we select a Trotter step count that improves quantum simulation fidelity under realistic processor noise?**

## Experimental Setup

- Model: Four-qubit transverse-field Ising model (TFIM), periodic boundary conditions
- Couplings: J = 1, g = 1
- Initial state: |1010⟩
- Evolution time: T = 2
- Method: First-order Trotterization
- Trotter steps: 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16
- Processors: A, B, and custom Processor D
- Noise scales: 0.5×, 1×, 2× for Processor D
- Measurement shots: 4096

## Main Results

### Noise-Aware Optimization

| Processor D noise scale | Optimal Trotter steps |
|---|---:|
| 0.5× | 8 |
| 1× | 7 |
| 2× | 6 |

Increasing noise shifts the optimal circuit depth toward fewer Trotter steps.

### Advisor Performance

On five additional simulated noise settings:

| Strategy | Exact matches | Mean fidelity regret |
|---|---:|---:|
| Q-OPTIMA quadratic advisor | 3/5 | 0.000422 |
| Linear advisor | 2/5 | 0.001943 |
| Fixed 6 steps | 2/5 | 0.009714 |
| Fixed 7 steps | 1/5 | 0.010040 |
| Fixed 8 steps | 1/5 | 0.024877 |
| Fixed 16 steps | 0/5 | 0.187292 |

Q-OPTIMA achieved approximately 95.7% lower mean fidelity regret than the strongest fixed-step baseline evaluated.

These results are specific to the tested processor, Hamiltonian, and noise settings.

## Additional Experiments

- Bell-state verification on adjacent and nonadjacent qubit pairs
- Circuit resource and routing-overhead analysis
- Approximation-versus-noise error decomposition
- Comparison of linear and quadratic noise-penalty models
- Independent simulation-based advisor evaluation

## Project Structure

```text
Q-OPTIMA-2026/
├── main.ipynb
├── ps_s3_simulation.py
├── run_s3_benchmark.py
├── run_bell.py
├── error_decomposition.py
├── trotter_advisor.py
├── validate_advisor.py
├── advisor_v2.py
├── final_advisor_test.py
├── v2_fixed_step_test.py
├── validate_q_optima.py
├── processors/
│   └── processor_D.json
├── starter/
│   └── qff_sim.py
├── results/
│   ├── tables/
│   └── figures/
└── requirements.txt
```

Additional validation and plotting scripts are included in the repository.

## Installation

Python 3.12 is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The working development environment used:

- Python 3.12.10
- Qiskit 2.5.2
- Qiskit Aer 0.17.2
- NumPy 2.5.4
- SciPy 1.18.1
- Matplotlib 3.11.2

## Reproduction

Open `main.ipynb` in VS Code or Jupyter, select the Python environment, and run all cells.

Alternatively:

```powershell
python run_s3_benchmark.py
python run_bell.py
python error_decomposition.py
python final_advisor_test.py
python v2_fixed_step_test.py
python validate_q_optima.py
```

The scripts generate numerical results under `results/tables/` and figures under `results/figures/`.

## Limitations

Q-OPTIMA is evaluated using classical quantum-circuit simulation, not a physical quantum computer. Its advisor has been tested primarily on a single four-qubit Hamiltonian and custom processor. The quadratic noise model is empirical rather than a universal physical law.

## AI Assistance Disclosure

Generative AI assisted with code drafting, debugging, experiment planning, documentation, and interpretation. The reported numerical results were generated and checked by executing the simulation scripts.

## Competition Submission

