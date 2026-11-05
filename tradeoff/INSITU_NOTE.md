# Additional direct in-situ comparison

Before completing or inspecting aggregate results of the primary campaign,
add a direct secondary experiment for the original online semantics.
Reuse the unchanged executable and model. For each method, run its calibration
calls and enough additional committed calls that their sum is exactly H.
For example, H=50 gives Full 12 thirty-six tuning/useful calls plus fourteen
committed calls; Guided 4 gets twelve plus thirty-eight. All fifty advance
the useful-work counter in this interpretation of the repeated kernels.

Measure H=50 and H=500 independently, for Prior only, Guided 4, and Full 12,
on all 24 scenarios in three new randomized blocks. The native phase totals
provide direct tuning-plus-payload wall/CPU cost; this is not reconstruction
from old prefixes or simulated timing. Report these ratios separately from
the extra-calibration primary experiment. Do not credit avoided calibration
as avoided necessary work.
