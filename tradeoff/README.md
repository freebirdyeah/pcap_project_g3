# Budgeted OpenMP scheduling study

The experiment compares the time and CPU cost of selecting an OpenMP scheduler with the resulting execution quality. The final paper is in `deliverables/current/`.

- `src/tradeoff.cpp`: experiment and selection implementation; includes the shared kernels in `../src/experiment.cpp`.
- `study.py`, `insitu.py`: measurement campaigns.
- `analyze.py`, `analyze_insitu.py`: analysis of recorded measurements.
- `data/`: current study measurements, protocol, and fitted model.
- `results/`: computed results.
- `paper/`: source and figures for the final paper.

## Build

The experiment requires Clang 16, CMake, Python packages from `../requirements.txt`, and an external LB4OMP checkout. The recorded study used LB4OMP commit `b9d25eca7265a4b5b3a675a1765d489775847938` with a Clang 16 portability adjustment. That runtime and adjustment are not included here.

From the repository root, set `LB4OMP_SOURCE` to a compatible checkout and run:

```bash
LB4OMP_SOURCE=/path/to/LB4OMP bash tradeoff/build.sh
```

The build creates `build/` locally. The recorded benchmark protocol assumes a particular machine and CPU affinity; new runs require adapting those settings. Existing measurement metadata records the original executable hash, so a newly built executable is not interchangeable with the original for resume or binary-hash audit purposes.
