# Reference uncertainty and additional sensitivity

The frozen primary analysis uses the independently measured best fixed-arm
median within each measurement block, as stated in RESEARCH_PLAN.md. A minimum
over 12 noisy medians is optimistic and can overstate residual slowdown.
It will be reported as an empirical reference, not a known optimum.

Add a cross-fitted sensitivity without changing any runtime policy: select the
reference arm using the other four blocks' medians and evaluate that arm's
time in the held-out block. This separates choosing the reference arm from
measuring its held-out time. Report both 5% and 10% acceptance rates under
both definitions. This is an analysis-only sensitivity, recorded while the
first fresh test block is running, before aggregate outcomes were inspected.

The protocol's `training` field records the previous study's full configuration
pool, including `split` flags. Only records with `split == train` (seeds 0 and
1, twelve scenarios) are used for this study's calibration and model fitting.
No records with the old test flags contribute labels to the fitted prior.
