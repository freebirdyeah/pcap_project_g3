# Budgeted OpenMP scheduling: fresh cost–quality study

This artifact asks whether saving tuning wall time and CPU seconds is worth a
small loss in the speed of the committed scheduler. It preserves the earlier
continuous-bandit study and uses fresh measurements on seeds 4–7.

## Main outputs

- `paper/PCAP_TRADEOFF_PAPER_G3.tex` and its PDF: standalone new manuscript.
- `RESEARCH_PLAN.md`: protocol fixed before new test measurements.
- `REFERENCE_NOTE.md`: declared reference-uncertainty sensitivity.
- `INSITU_NOTE.md` and `insitu.py`: separate direct comparison in which tuning
  calls also advance useful work; each policy executes the same total calls.
- `src/tradeoff.cpp`: native phase instrumentation and budgeted selection.
- `data/protocol.json`: fixed budgets, horizons, groups, seeds, source hashes.
- `data/prior_cost.json`: directly measured operational acquisition cost.
- `data/calibration/`, `data/reference/`, `data/online/`: immutable raw CSVs,
  phase summaries, whole-process resource usage, checksums, and hashes.
- `results/report.json` and aggregate CSVs: auditable numerical results.
- `analyze.py`: complete-corpus validation, cost/quality analysis, bootstrap,
  cross-fitted references, crossover and amortization, and figures.
- `render_results.py`: manuscript numbers and tables generated from the report.

## What is actually measured

Calibration is **extra work before useful execution**. Guided 2/4/8 test that
many candidates, including STATIC, with three calls per candidate. Prior only
uses three STATIC probes and predicts the committed scheduler. Full search
measures all twelve candidates three times each. Every policy then performs
the same 500 useful loop executions; prefixes report horizons 10/50/100/500.

Process CPU seconds use `CLOCK_PROCESS_CPUTIME_ID` and include all OpenMP
threads and active waiting in measured phases. They are not energy or FLOPs.
Fewer calibration calls are not automatically assumed to save proportional
time or CPU. Actual phase consumption is recorded.

Each of five randomized blocks interleaves 168 policy jobs and 288 independent
fixed-arm reference jobs. There are 24 scenarios and 12 input configuration
clusters. References are used only after committed selections are logged.
The primary empirical best is a minimum over independent same-block medians;
the cross-fitted sensitivity chooses the arm in other blocks and evaluates it
in the held-out block. Neither is a mathematical Oracle.

## Reproduce

Run from the enclosing artifact root. Requirements are Clang 16, CMake, Make,
Python with the packages pinned in `requirements.txt`, and pdflatex.

```bash
bash tradeoff/build.sh
```

The build reuses the pinned public LB4OMP runtime (retrieved with
`scripts/build.sh` if absent). Its portability patch is in `patches/`.
The shared audited kernels/model code is in `src/experiment.cpp`; the old
experiment entry point is renamed during compilation and is not run.

To perform a **new** measurement campaign, use a separate artifact copy with
empty `tradeoff/data` outputs. The frozen protocol/model reject accidental
replacement. Existing completed jobs can resume without modifying data.

```bash
OPENBLAS_NUM_THREADS=1 python3 tradeoff/study.py freeze
OPENBLAS_NUM_THREADS=1 python3 tradeoff/study.py calibrate
OPENBLAS_NUM_THREADS=1 python3 tradeoff/study.py fit
OPENBLAS_NUM_THREADS=1 python3 tradeoff/study.py evaluate
OPENBLAS_NUM_THREADS=1 python3 tradeoff/insitu.py
```

The hard-coded affinity assumes physical-core representatives 0,2,4,6.
Adapt it and record a new protocol on other hardware. Run sequentially and
avoid concurrent benchmark campaigns. The prior uses only training-tagged
configurations from the previous pool (seeds 0/1), never old or new test labels.

To analyze the supplied measurements and build the paper:

```bash
OPENBLAS_NUM_THREADS=1 python3 tradeoff/analyze.py
OPENBLAS_NUM_THREADS=1 python3 tradeoff/analyze_insitu.py
OPENBLAS_NUM_THREADS=1 python3 tradeoff/audit_final.py
OPENBLAS_NUM_THREADS=1 python3 tradeoff/render_results.py
cd tradeoff/paper
pdflatex -interaction=nonstopmode -halt-on-error PCAP_TRADEOFF_PAPER_G3.tex
pdflatex -interaction=nonstopmode -halt-on-error PCAP_TRADEOFF_PAPER_G3.tex
```

Selection costs, payload slowdown, total deployment wall/CPU cost, and offline
amortization are separate outputs. The comparison with Full 12 includes that
method's tuning cost; the comparison with the empirical best evaluates payload
quality only. The paper does not require beating the reference scheduler.

## Interpretation limits

This is a four-core WSL2 study with compact stationary kernels. The primary
extra-calibration savings must not be transferred to in-situ execution; use the
separate equal-useful-work results for that interpretation. The study does not
establish generalization to unseen application families or HPC machines. It excludes method
development and compilation cost from operational prior acquisition. Acquisition
is separately charged for both the trained fixed arm and model-based policies.
Near-best quality is an empirical estimate with uncertainty, not a guarantee.

## Measured outcome

Guided 4 saved 65.0% of tuning wall time and 65.9% of tuning CPU time.
With a cached prior and 50 useful executions, total wall and CPU cost ratios
(Full 12 / Guided 4) were 1.379 and 1.384: approximately 27.5% less elapsed
time and 27.8% fewer CPU seconds. Its extra payload slowdown relative to
Full 12's chosen arm was -1.1% (95% interval -3.3% to +0.9%), so these
measurements did not establish an extra throughput penalty against that
feasible comparator.

Absolute proximity to an optimum is less certain. The same-block empirical
best gives Guided 4 a 10.2% geometric residual; only 44.2% of runs are within
5%. The cross-fitted reference changes that hit rate to 85.0%, demonstrating
reference sensitivity rather than a guarantee of optimality.

Operational prior acquisition cost 35.97 wall seconds and 83.89 CPU seconds.
At the 50-execution horizon, the estimated amortization counts for Guided 4
are 488 deployments for wall time and 409 for CPU time.

When tuning executions count as useful work, Guided 4's wall ratios are
0.970 at 50 useful calls and 1.000 at 500; the new direct comparison does
not establish an in-situ time/CPU saving. The large primary savings concern
additional calibration and must not be transferred to that operating mode.

The final audit covers 3,144 processes and 595,896 logged executions across
fresh calibration, independent references, the primary policies, and the
equal-useful-work comparison. It verifies 6,288 raw/summary hashes and the
unchanged frozen source, binary, and model. See `results/final_audit.json`.
