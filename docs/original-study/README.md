# Group 3 — OpenMP scheduler selection research artifact

This repository accompanies **Warm-Started Contextual Bandits for OpenMP
Scheduling: A Reproducible Single-Node Study** by Shaan Chopra, Mrinal Dhami,
and Aniket Verma. The original proposal is preserved as `PCAP_SYNOPSIS_G3.pdf`.

## Contents

- `paper/PCAP_RESEARCH_PAPER_G3.tex`: complete manuscript source.
- `src/experiment.cpp`: native C++ online selectors and benchmark kernels.
- `scripts/study.py`: sequential, randomized experiment orchestration.
- `scripts/fit.py`: training-only validation, model fitting, portfolio reduction.
- `scripts/analyze.py`: results, confidence intervals, figures, and audit checks.
- `scripts/audit.py`: complete-corpus hash, configuration, split, and frozen-model
  reproducibility checks.
- `scripts/transfer.py` and `scripts/analyze_transfer.py`: exploratory
  leave-one-workload-family-out measurements and analysis.
- `tests/numerics.cpp`: rank-one matrix update, independent graph verification,
  and coverage checks for every scheduler at both thread counts.
- `patches/lb4omp-clang16.patch`: portability-only change to the public runtime.
- `data/environment.json`: hardware, tool versions, affinity, and configurations.
- `data/protocol.json`: model and evaluation choices frozen before final tests.
- `data/calibration/`: training measurements; `data/reference/`: independent test
  fixed-arm reference; `data/online/`: actual online executions and metadata.
- `results/`: generated aggregate CSVs and `report.json`; all numerical claims
  originate in these files and their raw inputs.
- `RESEARCH_LOG.md`: decisions, pilot changes, and limitations.

## Build

Requirements: Linux x86-64, Clang/Clang++ 16, CMake, GNU Make, Python 3 with NumPy,
SciPy, pandas, and matplotlib. A minimal pdflatex installation builds the paper.
No GPU is required. Exact package versions are in `data/environment.json`.

```bash
bash scripts/build.sh
clang++-16 -O2 -std=c++17 -fopenmp \
  -I build/lb4omp-clang/runtime/src tests/numerics.cpp \
  -L build/lb4omp-clang/runtime/src \
  -Wl,-rpath,"$PWD/build/lb4omp-clang/runtime/src" -lomp -o build/numerics
KMP_CPU_SPEED=3200 KMP_Golden_Chunksize=1 \
  OMP_PLACES='{0},{2},{4},{6}' OMP_PROC_BIND=close build/numerics
```

The build script retrieves LB4OMP commit
`b9d25eca7265a4b5b3a675a1765d489775847938`. Its original LLVM/OpenMP and LB4OMP
licenses remain in the dependency checkout. The dependency is not relicensed.
The small patch replaces an invalid initialized variable-length array with a
zero-initialized vector. Runtime scheduler and Q-learning logic are preserved.

## Reproduce the measurements

The supplied raw measurements should be retained for comparison. To run a new
campaign, use a separate copy of this artifact with empty calibration,
reference, and online output directories. Existing outputs with metadata are
skipped so interrupted campaigns can resume. Do not refit a different model and
resume into an existing set of online outputs.

```bash
python3 scripts/study.py manifest
python3 scripts/study.py pilot
python3 scripts/study.py train
OPENBLAS_NUM_THREADS=1 python3 scripts/fit.py
python3 scripts/study.py reference
python3 scripts/study.py online
OPENBLAS_NUM_THREADS=1 python3 scripts/transfer.py
```

The code assumes physical-core representative CPU IDs 0, 2, 4, and 6. Change
`OMP_PLACES` in `scripts/study.py` and record a new environment manifest when
using different topology. Guest CPU numbering does not guarantee host
isolation. Each measurement runs sequentially; do not execute another benchmark
campaign at the same time.

Each process logs 500 online loop instances, a serial output-equivalence
check, wall-clock accounting, software configuration, and SHA-256 of the CSV.
The training/reference campaigns use three processes per scenario and arm,
each containing a common STATIC probe followed by 19 measured fixed-arm
executions. The held-out reference is used only for evaluation, never training.

## Reproduce the analysis and PDF

```bash
OPENBLAS_NUM_THREADS=1 python3 scripts/analyze.py
OPENBLAS_NUM_THREADS=1 python3 scripts/analyze_transfer.py
OPENBLAS_NUM_THREADS=1 python3 scripts/audit.py
python3 scripts/render_results.py
cd paper
pdflatex -interaction=nonstopmode -halt-on-error PCAP_RESEARCH_PAPER_G3.tex
pdflatex -interaction=nonstopmode -halt-on-error PCAP_RESEARCH_PAPER_G3.tex
```

`render_results.py` generates the manuscript's numerical text and tables from
`results/report.json`. These outputs are not manually entered benchmark data.
`results/paired_comparisons.csv` includes both raw and Holm-adjusted signed-rank
p-values. Bootstrap intervals resample input configurations rather than treating
300,000 primary loop instances as independent observations. The exploratory
transfer campaign adds 108 processes and 54,000 loop instances.
The full audit covers 1,572 processes and 371,280 logged instances, including
training and independent reference measurements. Its machine-readable output
is `results/validation/corpus_audit.json`.

## Interpretation

This is a measured single-node study under WSL2, not a reproduction of the
original paper's multi-socket cluster numbers. It uses original Mandelbrot,
Triad-style streaming, and sorted-intersection graph kernels. The streaming
and graph code are not the reference STREAM or GAP implementations. Test inputs
belong to the same three workload families as training inputs. The study does
not establish cross-application or cross-hardware generalization.

The measured warm/native-Q speed ratio is 1.011 (95% cluster-bootstrap
interval 0.954–1.057); warm/exhaustive is 1.002 (0.959–1.042). These results do
not demonstrate a warm-start advantage. The manuscript reports this outcome
alongside the fixed-policy, prior-only, and transfer controls. Its claims are
limited to the measured implementation and environment.

The empirical fixed-arm reference is noisy and is not a mathematical Oracle.
The native Q-learning baseline is the released runtime implementation; its
costs should not be equated with the inherent cost of every Q-learning design.
Offline data collection and fitting must be amortized over repeated deployment.
See the manuscript for the complete result interpretation and limitations.

No paper submission, public repository, DOI, or external publication has been
created. The listed authors should review the manuscript and venue-specific
AI assistance and authorship policies before submission.
