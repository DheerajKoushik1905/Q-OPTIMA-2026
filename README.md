# Q-OPTIMA ULTIMATE

### Noise-Aware Quantum Simulation, Trotter-Step Optimization, Processor Selection, and Zero-Noise Extrapolation

**Competition:** Qiskit Fall Fest 2026 — Phase 2
**Track:** Quantum Simulation
**Problem Statement:** PS-S3 — Noise Accumulation in Trotter Circuits
**Team:** 3AM ENGINEERS

---

## 1. Project Overview

Q-OPTIMA ULTIMATE is a quantum simulation project designed to investigate the trade-off between Trotter approximation error and hardware noise.

Increasing the number of Trotter steps generally improves the approximation of ideal time evolution. However, additional steps also increase circuit depth and the number of noisy quantum gates.

Therefore, the largest number of Trotter steps is not necessarily the best choice on noisy hardware.

Our project explores this trade-off using Qiskit simulations and provides:

- Noisy Trotter-circuit benchmarking.
- Comparison of quantum processor connectivity.
- A noise-aware Trotter-step advisor.
- Resource-aware processor recommendations.
- Validation against simulated fidelity results.
- Zero-Noise Extrapolation (ZNE) experiments.
- Reproducible Python scripts, datasets, plots, and a Jupyter notebook.

## 2. Quantum System

We simulate a four-qubit transverse-field Ising model with periodic boundary conditions.

The Hamiltonian is:

\[
H=-J\sum_{(i,j)\in E}Z_iZ_j-g\sum_{i=0}^{3}X_i
\]

where:

\[
E=\{(0,1),(1,2),(2,3),(3,0)\}
\]

The simulation parameters are:

| Parameter | Value |
|---|---|
| Number of logical qubits | 4 |
| Interaction strength, J | 1 |
| Transverse field, g | 1 |
| Initial state | \(\lvert1010\rangle\) |
| Total simulation time | 2 |
| Trotter method | First-order |
| Trotter step counts | 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16 |

The first-order Trotter approximation is:

\[
U(T)\approx\left(e^{-iH_{ZZ}T/n}e^{-iH_XT/n}\right)^n
\]

where \(n\) is the number of Trotter steps.

## 3. Processor Comparison

We evaluate three processor configurations.

| Processor | Physical qubits | Connectivity |
|---|---:|---|
| A | 5 | Branching tree |
| B | 9 | Heavy-hex-inspired |
| D | 4 | Four-qubit ring |

Processor D is a custom configuration designed by our team.

Its connectivity is:

- Qubit 0 connected to qubit 1.
- Qubit 1 connected to qubit 2.
- Qubit 2 connected to qubit 3.
- Qubit 3 connected to qubit 0.

The processor configuration and diagram are available at:

- `processors/processor_D.json`
- `processors/Processor_D_3AM_ENGINEERS.jpg`

The simulation uses the basis gates `rz`, `sx`, `x`, and `cx`.

The base noise model uses:

| Noise parameter | Value |
|---|---:|
| Single-qubit gate error probability | 0.001 |
| Two-qubit gate error probability | 0.005 |
| Readout error probability | 0.01 |

These are simulation assumptions, not measurements from physical quantum hardware.

## 4. Main Simulation Results

The project evaluates fidelity across different Trotter-step counts, processors, and noise scales.

Selected results from the saved simulation summary are:

| Processor | Noise scale | Best step count | Simulated noisy fidelity |
|---|---:|---:|---:|
| A | 1.0× | 6 | 0.577419 |
| B | 1.0× | 7 | 0.662816 |
| D | 0.5× | 8 | 0.782118 |
| D | 1.0× | 7 | 0.662816 |
| D | 2.0× | 6 | 0.503076 |

These results demonstrate that the preferred Trotter-step count depends on the noise conditions.

At the base noise scale, processors B and D achieve the same simulated fidelity in this experiment. Processor D uses fewer physical qubits.

At eight Trotter steps:

| Processor | Physical qubits | Two-qubit gates | Circuit depth | Routing overhead |
|---|---:|---:|---:|---:|
| A | 5 | 109 | 134 | 45 |
| B | 9 | 64 | 89 | 0 |
| D | 4 | 64 | 89 | 0 |

Processor D provides a compact four-qubit topology that directly supports the simulated ring interactions.

## 5. Noise-Aware Trotter Advisor

We developed empirical advisors to recommend a Trotter-step count without performing a complete noisy scan for every new noise setting.

### Advisor V1

The initial advisor uses a linear noise-penalty approximation.

### Advisor V2

The improved advisor uses a quadratic step-dependent penalty:

\[
\widehat E(n,s)=1-F_{\mathrm{ideal}}(n)+\alpha sn^2
\]

where:

- \(n\) is the Trotter-step count.
- \(s\) is the noise scale.
- \(F_{\mathrm{ideal}}(n)\) is the ideal Trotter fidelity.
- \(\alpha\) is an empirically fitted coefficient.

The quadratic penalty is an empirical prediction model, not a claim that all physical quantum noise grows quadratically.

### Held-Out Validation

The advisor was evaluated on five held-out noise settings:

`0.4, 0.9, 1.25, 1.8, 2.8`

| Method | Exact step-count matches | Mean fidelity regret |
|---|---:|---:|
| Advisor V1 | 2/5 | 0.001943 |
| Advisor V2 | 3/5 | 0.000422 |
| Fixed 6 steps | — | 0.009714 |
| Fixed 7 steps | — | 0.010040 |
| Fixed 8 steps | — | 0.024877 |
| Fixed 16 steps | — | 0.187292 |

Advisor V2 produced lower mean fidelity regret than these tested baselines.

The evaluation is limited to five held-out settings under the simulated model.

## 6. Ultimate Hybrid Advisor

The Ultimate Hybrid Advisor combines:

1. Noise-aware Trotter-step prediction.
2. Processor resource comparison.
3. Two-qubit gate-count evaluation.
4. Physical-qubit requirements.
5. A processor and step-count recommendation.

For the tested configurations, it recommends Processor D.

| Noise scale | Recommended steps | Two-qubit gates | Physical qubits |
|---|---:|---:|---:|
| 0.4× | 8 | 64 | 4 |
| 0.5× | 8 | 64 | 4 |
| 0.9× | 7 | 56 | 4 |
| 1.0× | 7 | 56 | 4 |
| 1.25× | 7 | 56 | 4 |
| 1.8× | 6 | 48 | 4 |
| 2.0× | 6 | 48 | 4 |
| 2.8× | 6 | 48 | 4 |

The hybrid advisor agrees with the V2 step predictor on all five compared held-out settings. This represents agreement between the two methods, not five correct predictions against the simulated optimum.

A separate predictive advisor was also evaluated. Its held-out performance was weaker, with 1/5 exact step-count matches and mean fidelity regret of 0.003604. We retain this result for transparency.

## 7. Zero-Noise Extrapolation Extension

We additionally investigated Zero-Noise Extrapolation (ZNE) as an error-mitigation extension.

ZNE estimates a lower-noise observable by combining measurements or simulations performed at different effective noise levels.

The experiments compare raw noisy observables against ZNE estimates, using the ideal Trotter observable as the reference.

### Validation Experiment

Across 20 simulated trials:

| Metric | Result |
|---|---:|
| Trials | 20 |
| Trials with reduced error | 20 |
| Mean raw observable error | 0.183214 |
| Mean ZNE observable error | 0.073224 |
| Mean error reduction | 60.03% |

### Robustness Experiment

| Trotter steps | Improved trials | Mean raw error | Mean ZNE error | Error reduction |
|---|---:|---:|---:|---:|
| 7 | 20/20 | 0.177074 | 0.063891 | 63.92% |
| 8 | 20/20 | 0.208288 | 0.092614 | 55.54% |

These results support the effectiveness of the tested ZNE procedure for reducing observable error under the simulated conditions.

**Important distinction:** ZNE improves the estimated observable in these experiments. It does not physically remove gate noise or demonstrate an equivalent improvement in quantum state fidelity.

## 8. Repository Structure

```text
Q-OPTIMA-2026/
│
├── README.md
├── main.ipynb
├── requirements.txt
│
├── advisors/
│   ├── advisor_v2.py
│   ├── trotter_advisor.py
│   ├── ultimate_hybrid_advisor.py
│   ├── ultimate_predictive_advisor.py
│   └── ultimate_processor_advisor.py
│
├── experiments/
│   ├── ps_s3_simulation.py
│   ├── run_s3_benchmark.py
│   ├── run_bell.py
│   ├── make_s3_graphs.py
│   ├── error_decomposition.py
│   ├── v2_baseline_comparison.py
│   ├── v2_fixed_step_test.py
│   ├── zne_s3_validation.py
│   └── zne_s3_robustness.py
│
├── validation/
│   ├── test_setup.py
│   ├── test_noisy.py
│   ├── validate_q_optima.py
│   ├── validate_advisor.py
│   ├── final_advisor_test.py
│   └── ultimate_validation.py
│
├── processors/
│   ├── processor_D.json
│   └── Processor_D_3AM_ENGINEERS.jpg
│
├── results/
│   ├── tables/
│   └── figures/
│
├── starter/
│   └── qff_sim.py
│
└── tools/
    └── create_processor_d_jpeg.py
```

The repository also includes technical PDF reports and additional supporting result files.

## 9. Quick Reproduction

### Prerequisites

- Python 3.12
- Qiskit
- Qiskit Aer
- NumPy
- SciPy
- Matplotlib
- Jupyter

Install the dependencies from the repository root:

```bash
python -m pip install -r requirements.txt
```

### Run the Main Notebook

Open:

```text
main.ipynb
```

Select a Python environment containing the dependencies and run the notebook cells in order.

The notebook integrates the simulation workflow, processor comparison, advisor evaluation, and supporting experiments.

### Run the Main Benchmark

```bash
python experiments/run_s3_benchmark.py
```

### Generate the Figures

```bash
python experiments/make_s3_graphs.py
python experiments/error_decomposition.py
```

### Run the Hybrid Advisor

```bash
python advisors/ultimate_hybrid_advisor.py
```

### Run ZNE Validation

```bash
python experiments/zne_s3_validation.py
```

### Run ZNE Robustness Tests

```bash
python experiments/zne_s3_robustness.py
```

### Run Validation Scripts

```bash
python validation/test_setup.py
python validation/test_noisy.py
python validation/validate_q_optima.py
python validation/validate_advisor.py
python validation/final_advisor_test.py
python validation/ultimate_validation.py
```

All commands are intended to be run from the repository root. The reorganized scripts should be verified after relocation before relying on these commands.

## 10. Important Output Files

### Main Simulation

- `results/tables/s3_scan.csv`
- `results/tables/s3_summary.csv`
- `results/tables/resources.csv`
- `results/tables/bell.csv`

### Advisor Evaluation

- `results/tables/advisor_final_validation.csv`
- `results/tables/v2_fixed_step_comparison.csv`
- `results/tables/v2_fixed_step_scan.csv`
- `results/tables/ultimate_hybrid_recommendations.csv`
- `results/tables/ultimate_validation.csv`

### ZNE Evaluation

- `results/tables/zne_s3_validation.csv`
- `results/tables/zne_s3_robustness.csv`
- `results/tables/zne_s3_robustness_summary.csv`

### Figures

- `results/figures/noise_crossover.png`
- `results/figures/processor_comparison.png`
- `results/figures/error_decomposition.png`

## 11. Technical Reports

The repository contains reports documenting the quantum model, noise assumptions, experimental methodology, and evaluation results.

The primary reports are:

- `Q_OPTIMA_ULTIMATE_Final_Technical_Report.pdf` — Ultimate advisor and main technical evaluation.
- `Q_OPTIMA_ULTIMATE_ZNE_Final_Technical_Report.pdf` — ZNE extension and validation.
- `REPORT OF THE SOLUTION.pdf` — Original solution report.

These reports provide additional details beyond the README.

## 12. Limitations

- All reported experiments use quantum simulation rather than measurements from actual IBM quantum hardware.
- The noise models are simplified and may not represent all physical error mechanisms.
- The advisor validation uses a limited number of held-out noise settings.
- The empirical advisor is not guaranteed to generalize to other Hamiltonians, processors, or noise models.
- Processor recommendations depend on the tested configurations and resource criteria.
- ZNE results demonstrate improvements in selected observable estimates, not universal error mitigation.
- Additional hardware testing and larger-scale validation are needed before deployment claims can be made.

## 13. AI Assistance Disclosure

AI-assisted tools were used during development to support code drafting, debugging, documentation, and experiment planning.

The team was responsible for running the simulations, reviewing the results, checking the outputs, and preparing the submission.

All reported numerical results are based on the project's saved experiments rather than claimed physical-hardware measurements.

## 14. Team — 3AM ENGINEERS

| Member | Role |
|---|---|
| Dheeraj Koushik | Team Lead |
| Sampurna Biswas | Team Member |
| Rishi Matam | Team Member |
| Sachin Sreenivas | Team Member |
| Dhruv Om | Team Member |
| Giri Samarth | Team Member |

## 15. Project Repository

GitHub: https://github.com/DheerajKoushik1905/Q-OPTIMA-2026

**Q-OPTIMA ULTIMATE — Finding practical Trotter-step and processor choices under simulated quantum noise.**
