# Research record

## Objective
Complete Group 3's OpenMP scheduling selection project with executable code,
measured data, statistical analysis, and a publication-style manuscript.
Authors: Shaan Chopra (240905140), Mrinal Dhami (240905026), Aniket Verma
(240905156). Do not submit or contact third parties without a further request.

## Environment and initial decisions
- Available machine: AMD Ryzen 5 7235HS, four physical cores/eight logical CPUs,
  7.6 GiB RAM, Linux under WSL2. Host activity, turbo, and physical temperature
  cannot be controlled from this environment; record these as limitations.
- Original editable synopsis is no longer present; preserve PCAP_SYNOPSIS_G3.pdf.
- Downloaded public LB4OMP commit b9d25eca7265a4b5b3a675a1765d489775847938.
- GCC 13 cannot build LB4OMP's anonymous aggregates containing C++ objects.
  Clang 16 is available; use it. Its rejection of an initialized variable-length
  array requires a one-line std::vector portability patch, archived in patches/.
  OMPT must remain enabled because upstream places LB4OMP setting handlers inside
  its OMPT preprocessor block. No scheduling or learner logic is changed.
- Warm-start contextual bandits are established (Oetomo et al., KAIS 2023).
  The contribution is an empirical OpenMP study, not a new bandit theorem.
- Native C++ selection is required to measure overhead without Python in the
  timed online path. Python handles orchestration, fitting, and analysis only.
- Results may refute the synopsis hypotheses. Report every baseline and failure.

## Protocol to freeze before test measurement
Use all 12 scheduling algorithms in the reference portfolio. Compare STATIC,
GSS, training-best fixed arm, exhaustive search, published native Q-learning,
context-free UCB, cold LinUCB, warm LinUCB, and warm reduced-portfolio LinUCB.
Every policy receives the same initial STATIC probe and warm-up budget.
The online horizon is 500, with summaries at 50, 144, and 500. No counterfactual
runtime is fabricated or replayed as a live execution.

Use three workload families: Mandelbrot, a Triad-style streaming kernel, and
original sorted-adjacency triangle counting on seeded graphs. The latter two
are inspired by STREAM and GAP but are not their reference implementations.
Use two independent training configurations and two held-out configurations
per family, each at two and four physical-core threads (12 train, 12 test).
Configuration-level splits keep all related observations together. The small
number of input configurations limits claims about unseen applications.

Primary endpoint: sum of observed loop and selector time over 500 instances,
normalized within scenario to independent fixed-arm reference measurements.
Also report paired speed ratios against exhaustive search, native Q-learning,
and best training arm; bootstrap at scenario level, not at individual loops.
Separate measured wall-clock results from oracle-relative estimated regret.
Make no 5%-convergence claim unless independent uncertainty supports it.

Exact configuration and tuning choices will be serialized before final test
runs; raw outputs will remain immutable and hashed in the artifact manifest.

## Pilot adjustment before freezing
The 4,096-vertex graph pilot costs about 8--10 ms per loop, whereas Triad costs
0.2--0.3 ms and Mandelbrot about 0.6 ms at four threads. Reduced graph sizes to
512/2,048 training and 1,024/1,536 test vertices before final calibration. Preserve
the interrupted larger-input calibration as pilot_calibration_v0. No final test
observations were used to choose sizes. Graph kernels are intentionally small
and cache-resident; do not infer large-graph performance from these results.

## Resume and exploratory transfer check
The user interrupted the turn during the fourth primary run block. There were
411 completed online processes with metadata at resume; finished outputs are
retained, and the sequential orchestrator resumes missing jobs. This interruption
creates a temporal break in the fourth block and is documented as such.
Added an explicitly exploratory leave-one-workload-family-out test: refit the
same prior on the two other training families, keep the primary hyperparameters,
and measure warm LinUCB, prior greedy, and best fixed on the held-out family.
Use three randomized blocks and 500 instances. This extends the evidence on
transfer without modifying the primary protocol or refitting on test outcomes.

## Completed measurement outcomes
Primary campaign: 600 processes, 300,000 instances; all output checks passed.
Training and held-out fixed-arm reference: 432 processes each, 20 instances each.
Exploratory family-transfer campaign: 108 processes, 54,000 instances; all checks
passed. Primary warm/native-Q speed ratio is 1.010688 (95% cluster-bootstrap
interval 0.954472--1.056596); warm/exhaustive is 1.002413 (0.958969--1.041815).
Warm/best-fixed is 0.988871 (0.932076--1.031419). No primary warm comparison
has a Holm-adjusted p below 0.05. These are null/inconclusive results rather
than confirmation of the synopsis's anticipated speedup. No test data were used
to alter the frozen primary policy, portfolio, or hyperparameters.
An exploratory sensitivity analysis removes the whole interrupted fourth block;
the corresponding intervals also include one. The manuscript discusses both
the 5.0% median between-run variability and the limited number of input clusters.

## Final audit
The corpus audit verified 1,572 hashes, process output checks, complete factorial
cells, and 371,280 finite logged rows across all four stages. It reproduced the
stored model and reduced portfolio from the training split without rewriting
the frozen files, and verified that their modification times predate the first
held-out reference measurement. Native numerical and scheduler-coverage tests
passed again after the campaigns. The paper compiles without warnings.
