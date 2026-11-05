# Result in deployment terms

The new paper evaluates less work spent selecting a scheduler, with the
chosen scheduler's quality measured separately. All values below come from
the new measured corpus.

## Extra calibration, cached prior

Four-candidate screening uses 12 calibration calls instead of 36 for Full 12.
It saves 65.0% of tuning wall time and 65.9% of tuning CPU seconds.

| Useful executions | Full-search wall cost / Guided 4 cost | CPU cost ratio |
| --- | ---: | ---: |
| 10 | 2.014 | 2.035 |
| 50 | 1.379 | 1.384 |
| 100 | 1.200 | 1.202 |
| 500 | 1.053 | 1.053 |

At 50 useful executions, these ratios correspond to about 27.5% less elapsed
time and 27.8% fewer CPU seconds. The wall-ratio 95% cluster-bootstrap interval
is 1.329–1.435; the CPU-ratio interval is 1.335–1.440.

## Execution quality

Relative to the arm actually chosen by Full 12, Guided 4's additional payload
slowdown is -1.1%, with interval -3.3% to +0.9%. The measurements do not show
an additional throughput penalty against that feasible full-search procedure.

That is not a guarantee of being within 5% of a true optimum. Relative to the
independent same-block empirical best, the geometric payload penalty is 10.2%
(interval 7.5%–13.3%); Full 12 itself has an 11.4% penalty against that noisy
reference. Guided 4 meets the 5% bound in 44.2% of runs and the 10% bound in
64.2%. Cross-fitting the reference changes these rates to 85.0% and 92.5%,
showing substantial reference sensitivity. The true optimum is not known.

## Paying for the prior

Operational acquisition cost was 35.97 elapsed seconds and 83.89 CPU seconds.
For the measured workload mixture and a 50-call useful horizon, Guided 4's
estimated amortization needs 488 deployments for wall time and 409 for CPU.
These are mean-cost estimates, not universal deployment guarantees. A fresh
prior for one short run is not economical in this implementation.

## Exploration that already advances useful work

This was measured directly in a separate experiment, with every method
executing exactly the same total number of useful calls, including tuning.
Guided 4's full-search/policy wall ratios were:

- 50 useful calls: 0.970, interval 0.933–0.999; about 3.1% slower in point estimate.
- 500 useful calls: 1.000, interval 0.987–1.013; essentially tied.

Thus the large extra-calibration savings do not apply to the original in-situ
interpretation. No time/CPU advantage is established there.

## Practical conclusion

Reduced search is worthwhile for avoiding additional calibration when a prior
is available and the application's quality tolerance permits the selected
schedule. It is not automatically worthwhile for one-off prior acquisition,
strict optimality requirements, or in-situ exploration. Simpler fixed and
random-budget controls also save search work; these results do not establish
that contextual prediction is necessary for the benefit.
