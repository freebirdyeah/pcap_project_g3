# Presentation outline — approved

Status: approved by the user's “go ahead”; remaining confirmation steps waived. Slide generation is authorized.

Audience: undergraduate presenters and a professor unfamiliar with this study.
Delivery: patient explanations, one main point per slide, approximately 15–20 minutes.
Count: 24 short slides. Numbers below identify the outline; no slide numbers will appear on slides.

## Reference and requested appearance

- Named template: Simple Light Mode.
- Retained source: `/home/shaan/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-simple-light-mode/assets/reference.pptx`.
- Inspected visual reference: the template's `assets/preview.png`.
- Keep the retained reference unchanged. Its typography is Helvetica Neue; use the reference's plain white/light visual system.
- User deviations: a single bold, large, top-left heading on every slide; left-aligned body bullets; no supertitles, slide numbers, decorative frames, decorative margins, or recurring footer chrome.
- Equations and charts centered below the explanation. Simple pale boxes only for a necessary definition or reminder.
- Maximum three short main bullets on normal slides. No dense paper screenshots or decorative imagery.
- No separate cover, agenda, or thank-you slide: start with the problem and end with the conclusion.
- Paper title, Group 3, and author names belong in the presentation metadata and speaker notes rather than an additional title slide.
- Available capability: Codex PPT. Its workflow produces full-slide images assembled into a PowerPoint; individual chart and text objects will not be separately editable.

## Source of truth

- `tradeoff/paper/PCAP_TRADEOFF_PAPER_G3.tex`
- `tradeoff/paper/results.tex`
- `tradeoff/paper/selection_table.tex`
- `tradeoff/paper/quality_table.tex`
- `tradeoff/paper/deployment_table.tex`
- `tradeoff/paper/insitu_table.tex`
- `tradeoff/results/report.json`
- `tradeoff/results/insitu_report.json`
- `docs/explanation/PCAP_PAPER_EXPLAINED_G3.md`

All percentages refer to this measured study. Hypothetical examples must be labeled as examples. Literature summaries come from the manuscript's cited background; avoid importing unrelated performance claims.

## Slide 1 — Choosing how to work also takes work

Visible bullets:
- CPU threads are workers. A scheduler divides the work between them.
- There are 12 scheduling options to choose from.
- Testing every option can cost more time than it saves.

Visual: a small centered four-worker / pile-of-tasks schematic, only if it adds clarity; otherwise text alone.
Reminder box: “Our question: can we make the choice more cheaply?”
Role: problem, immediately understandable without OpenMP knowledge.

## Slide 2 — Our workflow in one picture

Visible bullets:
- Learn from earlier jobs.
- Test a short list on the new job.
- Pick one option and keep using it.

Centered workflow:
“New job” → “Three basic checks” → “Model suggests three options” → “Test four options total” → “Use the fastest measured option”.
Small second input: “Earlier examples” → “Model”.
Reminder box: “The basic STATIC option is included in the four.”
Role: workflow. Keep the diagram deliberately simple; do not imply the model knows the winner in advance.

## Slide 3 — What earlier research gives us

Visible bullets:
- LB4OMP (2022): a library with several ways to divide loop work.
- Auto4OMP (2022): automatically choose a scheduler and its batch size.
- Comparative study (2025): compares selection strategies and examines exploration cost.

Reminder box: “We reuse existing schedulers and study the cost of choosing.”
Role: literature review. Speaker notes name the authors and explain “batch size” as how many tasks a worker receives at once.
Sources: manuscript references LB4OMP, Auto4OMP, and the 2025 comparative study. Exact citations in notes, no citation-number footer.

## Slide 4 — Our goal is to spend less on choosing

Visible bullets:
- Try fewer scheduling options.
- Measure both elapsed time and processor time.
- Check whether the final choice is still fast enough.

Reminder box: “Success means a cheaper overall job, with an acceptable speed trade-off.”
Role: research objective. Do not promise superiority to an unknown true optimum.

## Slide 5 — The three jobs we tested

Visible bullets:
- Mandelbrot: calculate image pixels; some pixels take longer.
- Array arithmetic: repeat the same simple calculation across a large list.
- Triangle counting: find groups of three connected graph points.

Centered, optional small equation for the arithmetic task: aᵢ = bᵢ + 3cᵢ.
Reminder box: “Different jobs create different work-sharing problems.”
Role: workloads. State in notes that these are small original kernels, not the reference STREAM or GAP implementations.

## Slide 6 — The machine and experiment

Visible bullets:
- AMD Ryzen 5 7235HS; four physical CPU cores; WSL2 Linux.
- Tested with two and four threads using C++ and OpenMP.
- 24 test scenarios, seven methods, five repeated blocks: 840 main runs.

Reminder box: “One machine and three workload families: the conclusions have that scope.”
Role: hardware and study design. Notes explain that there are 12 distinct test inputs, each used at two thread counts; repeated loops are not independent applications.

## Slide 7 — What we compared

Visible bullets:
- Full 12: test every option three times — 36 test executions.
- Guided 4: test four options three times — 12 test executions.
- Also check smaller/larger budgets, prediction only, random choices, and one fixed choice.

Centered simple count chart: Full 12 = 36, Guided 4 = 12.
Reminder box: “A test execution means running the loop once to measure it.”
Role: comparators. Notes retain all seven actual methods, including Guided 2 and Guided 8.

## Slide 8 — First, learn from earlier jobs

Visible bullets:
- Measure every scheduler on separate training inputs.
- Learn which job characteristics suggest a good option.
- Freeze the model before measuring the new test jobs.

Centered workflow: “Old jobs + measured times” → “Small prediction model” → “New jobs”.
Reminder box: “The new test results were not training answers.”
Role: approach, training and fair evaluation.

## Slide 9 — Describe the new job with six numbers

Visible bullets:
- How big is the job, and how many threads are available?
- How long do three basic STATIC checks take?
- Do some threads finish much earlier than others?

Centered equation: x = [1, log₂N, log₂P, log₂T₀, L₀, V₀]ᵀ.
Reminder box: “x is just an information card for the job.”
Role: approach, features. Notes calmly define the constant, logarithms, imbalance, variation, transpose, and training-based standardization.

## Slide 10 — Turn speed into an easy training score

Visible bullets:
- Faster than STATIC gets a positive score.
- Slower than STATIC gets a negative score.
- Extreme scores are capped between −1 and +1.

Centered equation: r = clip(−log(T / T_STATIC) / log 4, −1, 1).
Small example box: “Twice as fast: +0.5. Same speed: 0. Twice as slow: −0.5.”
Role: approach, reward. The equation is the manuscript's reward with indices removed for readability, not a new formula.

## Slide 11 — Learn a simple prediction rule

Visible bullets:
- Fit one small scoring rule for each scheduler.
- Each rule learns how much the six job features matter.
- A stabilizing penalty prevents extreme coefficients.

Centered equations, stacked rather than squeezed into one line:
A = λI + wΣxxᵀ
b = wΣxr
θ = A⁻¹b
Reminder box: “This is ridge regression: a weighted sum with a penalty.”
Role: approach, fitting. Notes explain A, b, θ, w = 0.25, λ = 1 and matrix inverse without expecting hand calculations.

## Slide 12 — Predict, then verify the shortlist

Visible bullets:
- Multiply the job features by the learned weights.
- Rank the options by their predicted scores.
- Measure the shortlist; actual timings decide the winner.

Centered equation: predicted score = xᵀθ.
Reminder box: “The model suggests. Measurements choose.”
Role: approach, prediction and commitment. Notes explicitly state that this study does not continuously update or switch schedulers during the committed useful runs.

## Slide 13 — Evaluate the total cost

Visible bullets:
- Include the cost of preparing the model.
- Add the time spent choosing for this job.
- Add the time spent doing useful work.

Centered equation: Total cost = training cost / reuses + choosing cost + useful execution cost.
Small notation below: J(H,R) = C_prior/R + S + Σₜ₌₁ᴴ Tₜ.
Reminder box: “Stopwatch time and CPU time are measured separately.”
Role: total-cost equation. Notes explain that CPU seconds sum across threads and are not an energy measurement.

## Slide 14 — Check how good the final choice is

Visible bullets:
- Independently measure all 12 options as an evaluation reference.
- Compare the chosen scheduler's execution time with the fastest reference median.
- Keep this separate from the cost of searching.

Centered equations: slowdown = chosen time / reference time − 1; retained speed = 1 / (1 + slowdown).
Example box: “11 ms instead of 10 ms = 10% more time.”
Role: quality measurement. Notes explain the actual reference: min over 12 medians, each based on 25 runs; the reference is noisy and is not a proven optimum.

## Slide 15 — The model's choices were not always near-best

Visible bullets:
- Guided 4: 10.2% aggregate execution-time penalty to the independent reference.
- Within 5% of that reference in 44% of runs; within 10% in 64%.
- Compared with Full 12's actual choice, no clear extra execution-time penalty.

Centered quality chart: two clearly labeled bars, “Within 5%: 44.2%” and “Within 10%: 64.2%”.
Reminder box: “The independent reference and Full 12's selected option are different comparisons.”
Role: model results. Notes give the direct Guided 4-versus-Full 12 payload estimate −1.1%, interval −3.3% to +0.9%, and the reference sensitivity. Do not claim a statistically demonstrated speed advantage.

## Slide 16 — Choosing took about two-thirds less work

Visible bullets:
- Guided 4 used 12 test executions instead of 36.
- Choosing took 65.0% less elapsed time.
- Choosing consumed 65.9% fewer CPU seconds.

Centered two-bar comparison: selection elapsed saving 65.0%, selection CPU saving 65.9%.
Reminder box: “These savings are for choosing, not for the whole application.”
Role: search-cost result. Use the audited paired aggregate values rather than recomputing them from median milliseconds.

## Slide 17 — For short jobs, the complete process was cheaper

Visible bullets:
- After additional testing, every method completed the same 50 useful executions.
- Guided 4 used about 27.5% less total elapsed time.
- It also used about 27.8% fewer total CPU seconds.

Centered indexed chart: “Full 12: 100” and “Guided 4: 72.5” for elapsed time.
Reminder box: “Relative cost index, not seconds. Model already available; tests are extra work.”
Role: easily understood complete-job result. Notes retain the ratio 1.379 and explain 1 − 1/1.379; uncertainty interval 1.329–1.435. The indexed graphic is a visual restatement of the aggregate ratio, not an independently measured single job.

## Slide 18 — Longer jobs dilute the upfront saving

Visible bullets:
- Choosing is a one-time expense.
- Its share of the total shrinks as useful work grows.
- Any slower execution can eventually use up the saving.

Centered chart: useful executions 10, 50, 100, 500; approximate total elapsed savings 50.3%, 27.5%, 16.7%, 5.0%.
Small centered equation: crossover = choosing-time saving / extra time per useful execution.
Role: horizon and crossover. Notes include H* = (S_F − S_m)/ΔT and clarify that it applies only for a positive per-execution time gap. There is no universal 935-execution cutoff.

## Slide 19 — Preparing the model must also pay off

Visible bullets:
- Model preparation cost about 36 elapsed seconds and 84 CPU seconds.
- At 50 useful executions per job, the estimated payback is about 488 reuses for elapsed time.
- A new model for one tiny job is not economical here.

Centered equation: reuses needed ≈ preparation cost / saving per job.
Reminder box: “Measured workload mixture; CPU-time payback was about 409 reuses.”
Role: training cost and amortization. Notes give the exact ceiling formula and the requirement for positive mean savings.

## Slide 20 — The saving depends on what the tests count as

Visible bullets:
- Extra tests: Full 12 runs 36 + 50 times; Guided 4 runs 12 + 50.
- Tests already doing useful work: both methods must finish 50 total useful runs.
- In that second setting, fewer tests do not remove required work.

Centered comparison diagram, two rows:
“Extra testing: 86 versus 62 executions”
“Testing is useful work: 50 versus 50 executions”.
Reminder box: “Always compare the same amount of useful work.”
Role: interpretation. Counts are the actual policy budgets at a 50-useful-execution horizon, not measured seconds.

## Slide 21 — When tests were useful work, we found no saving

Visible bullets:
- We measured this separately using equal total useful work.
- At 50 useful runs, Guided 4 was about 3.1% slower in the point estimate.
- At 500 useful runs, the methods were essentially tied.

Centered simple chart: Full 12 / Guided 4 wall-cost ratios 0.970 at 50 and 1.000 at 500, with a reference line at 1.000.
Reminder box: “No demonstrated overall time-and-CPU benefit in this mode.”
Role: unfavorable result, plainly stated. Notes give uncertainty intervals and avoid claiming equivalence was statistically proven.

## Slide 22 — The simplest alternatives also worked well

Visible bullets:
- Randomly testing four options also saved substantial search work.
- Reusing one training-selected scheduler was competitive.
- These results do not establish that model ranking is necessary.

Centered comparison, H = 50 and cached training information: complete wall-cost ratios Full 12 / method: Guided 4 = 1.379; Random 4 = 1.403; Best fixed = 1.704.
Reminder box: “Above 1 means cheaper than Full 12. These are finite measured comparisons.”
Role: controls and honest attribution. Notes point out that the trained fixed choice also has a training cost.

## Slide 23 — When is the trade-off worth it?

Visible bullets:
- The tests must be additional work that can genuinely be avoided.
- The model must already exist or be reused enough to repay its cost.
- The chosen scheduler's execution quality must be acceptable.

Centered equation: time saved choosing > extra execution time + share of preparation cost.
Reminder box: “One machine, three workload families; no guarantee for every new program.”
Role: analysis and decision rule. This is the paper's worthwhile-exchange inequality with the prior charge included. Notes explain the noisy reference, 12 independent input clusters, and large occasional quality penalties.

## Slide 24 — Conclusion

Visible bullets:
- Testing four options cut choosing time and CPU use by about two-thirds.
- With extra tests and an available model, short jobs used about 28% less total time.
- No clear saving when tests already finished useful work; simpler choices were competitive too.

Reminder box: “A cheaper choice is useful only when the total job becomes cheaper.”
Role: conclusion. No new claims, decorative thank-you text, or slide number.

## Production requirements after approval

- Clone/import the retained template and keep the source unchanged; apply only the visual deviations explicitly requested by the user.
- Follow the preinstalled presentation capability's reference-image workflow and required sample step unless the user waives remaining confirmations.
- All diagrams and plots must preserve the audited numbers and their comparison direction. No invented accuracy metric or energy claim.
- No required paper figure screenshots: the proposed plots are simpler restatements of audited tables. Preserve numerical fidelity when creating them.
- Write patient speaker notes explaining every symbol used on a slide; keep visible slide text short.
- Validate every rendered slide for typography, equation fidelity, chart labels, contrast, truncation, unwanted slide numbers, and clutter.
- Return the final PowerPoint and a convenient viewing version if the capability supports one.
