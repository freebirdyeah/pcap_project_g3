# Budgeted scheduling selection: frozen design

## Question
How much tuning wall time and process CPU time can be saved by testing fewer
OpenMP schedulers, and what residual execution-speed penalty is paid? At which
execution horizons and prior-reuse counts is that exchange worthwhile?

The earlier 500-instance study and its artifacts are preserved. This is a fresh
study with new held-out inputs, direct CPU measurement, explicit tuning and
payload phases, and a new manuscript. Winning against the empirical best
scheduler is not the goal.

## Primary semantics
Tune-then-run: tuning calls are additional calibration executions; afterward
exactly H useful executions run with the committed scheduler. Report tuning
cost and payload quality separately and charge both to deployment cost. Do not
claim that exploratory calls are saved useful work under in-situ semantics.
We will discuss that alternative separately.

Use all 12 public LB4OMP schedulers, the same expChunk rule and CPU affinity as
the earlier study. Reuse its workload implementation without editing it.
Train on the original seeds 0 and 1, collecting fresh calibration measurements.
Keep w=0.25, lambda=1, alpha=0.025 from the previous training-only selection;
no new test labels tune these values.

Budgeted screening uses three STATIC probes for context, ranks the other arms
by the fitted disjoint linear model's predicted reward, and tests the top
q-1 arms, three observations each. For q=2,4,8 choose the lowest measured
median among those q arms, including STATIC. Full search tests all 12 with
three observations each. Prior-only selection executes three STATIC probes
and commits to the model's best predicted arm without testing every candidate.
Controls: training-best fixed arm (no tuning), random four-arm screening
(STATIC plus three uniformly sampled nonstatic arms), and full 12-arm search.

All policies perform two common untimed warm-ups and the same 500 useful
executions after commitment. Primary prefix horizons: 10, 50, 100, 500.
Budgets and tolerances 5%/10% are fixed before test measurement.

## Test configuration groups
Three families, seeds 4,5,6,7, two thread counts: 24 scenarios and 12 input
configuration clusters, disjoint from the earlier test seeds 2 and 3.
Mandelbrot pixels: 36,864; 57,600; 20,736; 43,264.
Triad elements: 524,288; 655,360; 458,752; 917,504.
Graph vertices: 768; 1,792; 1,280; 1,920.
Use five randomized measurement blocks. Each block includes independent
fixed-arm reference runs (all 12 arms; 25 payload observations each) and the
seven policy treatments. No concurrent benchmark campaigns.

## Metrics and interpretation
- Calibration evaluations and actual selection wall/CPU seconds.
- Selected scheduler payload median relative to the block-local empirical best
  fixed-arm median: slowdown and retained speedup. Negative observed losses
  are retained as noise, not clipped into an alleged guarantee.
- Total tuning-plus-H-payload wall time and CPU time, relative to full search.
- Fraction of runs with wall savings and a payload loss <=5% or <=10%.
- Horizon crossover from saved tuning time versus per-instance quality gap;
  label this as a stationarity-based estimate, not a direct measured guarantee.
- Prior training cost and reuse-count break-even. Count complete fresh
  calibration process costs plus fitting, and contrast with already-available
  priors. Do not hide offline work.

Bootstrap input configuration clusters, pairing policies within blocks and
thread counts. Interpret small gaps cautiously under WSL2. Report every
budget, random screening, and best fixed; do not select only favorable cells.
No energy, FLOP-count, hardware generalization, or worst-case optimality claim.
