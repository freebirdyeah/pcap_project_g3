## Slide 1: Choosing how to work also takes work

Imagine four people packing boxes. Giving each person the same number of boxes sounds fair, but some boxes may take much longer. A scheduler is the rule for deciding which worker gets which task. In our program, the workers are CPU threads and the tasks are loop iterations.

We used an existing OpenMP library with twelve scheduling options. We did not invent those options. Our question is about choosing between them. Trying every option takes time too, so finding the fastest option is only useful if its later benefit repays the search. That is the problem our Group 3 project studies.

## Slide 2: Our workflow in one picture

Read this diagram from left to right. A new job arrives. We first run three quick checks using a basic option called STATIC. The model uses those checks to suggest three other options. We test those suggestions, together with STATIC, and keep the fastest measured one.

The model learned from earlier jobs. It does not know the correct answer for this new job in advance. It only helps create a shortlist. Our main method is called Guided 4 because there are four candidates in that shortlist. Once it chooses a winner, it stops switching and uses that option for the remaining useful runs.

## Slide 3: What earlier research gives us

There are three pieces of background here. LB4OMP provides existing scheduling algorithms. Auto4OMP studies automatic scheduler selection and calculates a chunk size: the number of loop tasks given to a thread at once. A later comparative study evaluates selection strategies and discusses the cost of exploration, meaning trying options to learn about them.

Our contribution builds on those systems. We reuse the schedulers and ask how much measurement effort we actually need to spend. We also use a standard regression model, rather than claiming a new learning algorithm.

References: Müller Korndörfer et al., LB4OMP, IEEE TPDS 33(4), 830–841 (2022), doi:10.1109/TPDS.2021.3107775. Mohammed et al., Automated Scheduling Algorithm Selection and Chunk Parameter Calculation in OpenMP, IEEE TPDS 33(12), 4383–4394 (2022), doi:10.1109/TPDS.2022.3189270. Müller Korndörfer et al., A Comparative Study of OpenMP Scheduling Algorithm Selection Strategies, IEEE Access 13, 151216–151234 (2025), doi:10.1109/ACCESS.2025.3602234.

## Slide 4: Our goal is to spend less on choosing

We are trying to save the resources spent making the choice. That means measuring fewer options without making the final execution unacceptably slow. We measure both stopwatch time and CPU time, because a quick-looking process can still consume time on several cores.

The target is the complete cost, not just the speed of the final scheduler. A slightly slower scheduler can be worthwhile if it is much cheaper to identify. Conversely, skipping tests is not automatically a success: if the chosen option performs poorly afterward, the saving can disappear. We measure both sides of that exchange.

## Slide 5: The three jobs we tested

We used three small types of computation. Mandelbrot draws a mathematical image. Some pixels need many more calculations than others, so dividing pixels evenly may leave threads finishing at different times. The array task repeats a simple calculation: for position i, take b at i, add three times c at i, and store it in a at i.

The graph task counts triangles: three points that are all connected to each other. A point with many neighbors can require more work than another point. These are original compact test kernels, not the standard STREAM or GAP benchmark implementations. They let us study different work-sharing patterns on one machine.

## Slide 6: The machine and experiment

This was measured on an AMD Ryzen 5 7235HS with four physical cores, under WSL2 Linux. We used two or four threads, pinned to representative physical cores, and compiled C++ with Clang 16 and the LB4OMP OpenMP runtime. The expert chunk-size setting was enabled for every method.

We had twelve distinct test inputs: four from each workload family. Each was tested with two thread counts, making twenty-four scenarios. Seven methods and five repetition blocks give 840 main policy runs. Those repetitions improve measurement, but they do not create 840 independent applications. The findings have the scope of this machine and these workload families.

## Slide 7: What we compared

The main comparison is simple. Full 12 tests every one of twelve schedulers three times, giving thirty-six test executions. Guided 4 tests four schedulers three times, giving twelve executions. The three STATIC probes are already included in that twelve, so they are not charged twice.

The other methods check whether a simpler strategy could work just as well. We included Guided 2, Guided 8, a model prediction without testing its predicted winner, four candidates with random alternatives, and one training-selected fixed scheduler. Full 12 is a real finite search with noisy measurements. It is not a perfect mathematical oracle.

## Slide 8: First, learn from earlier jobs

Before evaluating new jobs, we collected training measurements. We measured every scheduler on separate inputs and fitted a small predictor. Training used seeds zero and one, and evaluation used new inputs with seeds four through seven. The model and choices were frozen before the final test measurements.

This separation matters because the model should not be handed the answers it will later be graded on. One training scenario contributes a median timing label per scheduler; individual loop rows are not treated as thousands of independent examples. We then reuse the fitted model to guide selection on the new jobs.

## Slide 9: Describe the new job with six numbers

The letter x means a small information card for the job. N is the number of loop iterations, and P is the number of threads. T with a zero is the median time of three STATIC checks. L describes how unevenly the threads finish. V describes the spread in their finish times. The first entry, one, gives the scoring rule a basic starting value.

Log base two compresses large ranges: doubling a quantity increases its logged value by one. The transpose symbol just means arrange these numbers as a column. Before prediction, the nonconstant features are scaled using training averages and standard deviations. There is no need to calculate them by hand during a presentation.

## Slide 10: Turn speed into an easy training score

The model needs a numerical target for each scheduler. T is its measured time, and T STATIC is the basic scheduler's time on the same training example. Divide those times to see whether it is faster or slower. The negative logarithm makes faster choices positive. Dividing by log four sets the scale.

Twice as fast gives positive one-half. The same time gives zero. Twice as slow gives negative one-half. Clip means stop the score going below minus one or above plus one. This limits the influence of extreme measurements. It is a training score, not a percentage saving or a guarantee about the whole job.

## Slide 11: Learn a simple prediction rule

This is standard ridge regression. We learn six weights for each scheduler, one for each of the six features. The table A summarizes feature relationships and includes a stabilizing penalty. The vector b connects features with the observed training scores. Theta is the resulting list of learned weights. The inverse notation means solve this regression calculation.

Lambda controls the penalty; I is the identity matrix, with ones on the diagonal. The weight w controls how strongly the training data contributes relative to that penalty. We used lambda equal to one and w equal to one-quarter, inherited from the earlier training-only validation. These formulas are bookkeeping for fitting a weighted sum, not a neural network.

## Slide 12: Predict, then verify the shortlist

Prediction is a weighted sum. Multiply each entry in the job's information card by its learned weight, then add the results. That is what x transpose theta means. A larger predicted score suggests a better scheduler relative to STATIC.

We use that ranking to pick the three most promising non-STATIC alternatives. Then we actually time them. For every tested scheduler, we use the median of its three timing observations and select the smallest. The predictor proposes the shortlist, while measurements decide the winner. In this paper, there is no continuously updating bandit during the useful execution phase. We make a choice and commit.

## Slide 13: Evaluate the total cost

Read the large equation as three expenses. First is preparing the model. If R jobs share that model, each gets a share C prior divided by R. Next is S, the time spent selecting a scheduler for the present job. Last is useful execution: add the time T for each of the H useful runs. The sigma symbol means add them all.

J is the total we compare. We do this separately for stopwatch time and CPU seconds. CPU seconds add consumption across the process's threads and include active waiting. They are not electricity use or a count of arithmetic operations. When we say the model is available, its preparation expense has already been paid and is considered separately.

## Slide 14: Check how good the final choice is

To judge the final scheduler, we collect independent reference measurements. For each scenario and repetition block, each of the twelve schedulers gets twenty-five reference executions. We take each scheduler's median, then choose the smallest median as an empirical comparison reference. Those results are not given to the selection model.

Slowdown is the chosen time divided by the reference time, minus one. Eleven milliseconds instead of ten is a ten-percent time penalty. Retained speed is one divided by one plus that penalty: about ninety-one percent here. This reference is noisy. In particular, picking the minimum of several noisy estimates can make the reference look especially fast. It is not a proven true optimum.

## Slide 15: The model's choices were not always near-best

Against that independent same-block reference, Guided 4 had a geometric aggregate execution-time penalty of 10.2 percent. It was within five percent in 44.2 percent of runs, and within ten percent in 64.2 percent. The ninety-percentile penalty was about thirty-one percent, so some cases were much worse than the average.

The direct comparison with the scheduler actually selected by Full 12 is different: minus 1.1 percent additional time, with an interval from minus 3.3 to plus 0.9 percent. That does not establish an extra execution-time penalty or a clear speed advantage. Full 12's own choice can be imperfect. An alternative cross-fitted reference changed the near-best rates substantially, so absolute optimality remains uncertain.

## Slide 16: Choosing took about two-thirds less work

Here we are looking only at the selecting phase. Guided 4 avoided twenty-four of Full 12's thirty-six test executions. Actual measurement showed 65.0 percent less elapsed selection time and 65.9 percent fewer CPU seconds. Loading the model and computing its ranking were included in the measured selection cost.

The time saving is not exactly the same as the count saving, because candidates can take different amounts of time and prediction itself has overhead. These are paired aggregate comparisons across the experiment, not a calculation from two median times. Most importantly, the sixty-five-percent saving is not a claim that the whole application became sixty-five percent faster.

## Slide 17: For short jobs, the complete process was cheaper

Now include choosing and doing the useful job. Every method first performs extra tests, then completes fifty useful executions. Assume the trained model is already available. Under those conditions, Guided 4 used about 27.5 percent less elapsed time and 27.8 percent fewer CPU seconds overall.

The chart uses a relative index. If Full 12's cost is represented by one hundred, Guided 4 is about seventy-two and a half. These are not seconds from one particular run. The underlying aggregate ratio is Full 12 divided by Guided 4, equal to 1.379. To turn it into a time reduction, calculate one minus one divided by 1.379. The ratio's interval was 1.329 to 1.435.

## Slide 18: Longer jobs dilute the upfront saving

Choosing is a one-time expense. For ten useful executions afterward, the aggregate elapsed saving was about fifty percent. At fifty it was twenty-seven and a half percent. At five hundred it was about five percent. These horizons are prefixes of the same long measured runs, not four independent campaigns.

If our scheduler takes extra time per useful execution, a crossover can eventually occur. Divide the upfront choosing-time saving by the extra time per execution to estimate how many runs use up that saving. This assumes stable average times and a positive later time penalty. Some comparisons had no such penalty. The paper's conditional median crossover of 935 executions is not a universal cutoff.

## Slide 19: Preparing the model must also pay off

The model was not free to acquire. Collecting the operational training measurements and fitting it took 35.97 elapsed seconds and 83.89 CPU seconds. This excludes compilation, earlier method development, and the earlier campaign that selected the inherited hyperparameters.

To estimate payback, divide preparation cost by the average seconds saved per job, then round up. For Guided 4 and fifty useful executions, that gave 488 reuses for elapsed time and 409 for CPU time. We use average saved seconds here because real seconds repay the expense. If average saving is zero or negative, no number of reuses repays it under that comparison. These counts depend on the measured workload mixture.

## Slide 20: The saving depends on what the tests count as

This is the most important interpretation check. If testing is additional work, Full 12 performs thirty-six tests and fifty useful runs: eighty-six executions. Guided 4 performs twelve tests and fifty useful runs: sixty-two. It really avoids twenty-four extra executions.

But suppose testing already completes part of the application's useful work. The application still needs fifty useful executions total. Full 12 can do thirty-six while testing and fourteen afterward. Guided 4 does twelve while testing and thirty-eight afterward. Both must do fifty. We cannot count fewer tests as fewer necessary useful runs. That is why we measured this second situation separately.

## Slide 21: When tests were useful work, we found no saving

This separate experiment gives every method the same total useful work, including its tests. It used new direct measurements rather than reconstructing an answer from the earlier cost table. At fifty useful executions, the Full 12 divided by Guided 4 elapsed ratio was 0.970: Guided 4 was about 3.1 percent slower in the point estimate. At five hundred, the ratio was approximately one.

The fifty-run elapsed ratio interval was 0.933 to 0.999, while the CPU interval included one. At five hundred, both intervals included one. These results do not establish an overall time-and-CPU saving in this mode. Being approximately tied also does not prove exact equivalence on every future job.

## Slide 22: The simplest alternatives also worked well

We included these controls because otherwise every improvement might be credited to the model. Random 4 still tries only four candidates, so it also avoids most search effort. Best fixed uses the training-selected SS scheduler without any online tests.

For fifty useful executions after extra tests, the full-search divided by method ratios were 1.379 for Guided 4, 1.403 for Random 4, and 1.704 for Best fixed. Above one means the method cost less than full search. These point estimates do not prove a universal ordering, but they show that learned ranking is not established as necessary. The fixed scheduler's training information also has an acquisition cost when it is not already available.

## Slide 23: When is the trade-off worth it?

The decision is to compare what we save while choosing with what we might lose afterward. The choosing-time saving must exceed any extra useful execution time plus the present job's share of model preparation cost. We must also decide what execution-quality penalty is acceptable.

This worked for avoiding additional calibration with an available model in our measured workload mixture. It did not show the same benefit when tests already did useful work. There are other limits: one four-core WSL2 machine, three small workload families, twelve independent test input configurations, and noisy timing references. We should present this as a conditional engineering result, not a guarantee for every program or a proven optimum.

## Slide 24: Conclusion

Our project shows that measuring fewer scheduling candidates can substantially reduce the work spent choosing. Guided 4 saved about two-thirds of selection time and CPU consumption. When those tests were extra and the trained model was already available, fifty useful runs afterward cost about twenty-eight percent less elapsed time overall.

The conditions are part of the result. Preparing the model needs reuse to repay its expense. If testing already finishes useful work, we found no clear overall saving. Simple random and fixed choices also performed competitively. The practical contribution is measuring the complete cost and quality exchange, so a user can decide whether a cheaper selection process is worthwhile for their situation.
