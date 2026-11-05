The paper asks one practical question:

> **“Can we spend less time choosing how to run a program, while still choosing a reasonably fast option?”**

The answer from our experiments is: **yes, when choosing involves extra test runs and we reuse the trained model. When those test runs already help finish the actual job, we found no clear benefit.**

Here is the whole [current paper](/home/shaan/pcap/deliverables/current/PCAP_TRADEOFF_PAPER_G3.pdf), step by step. The numerical examples below are teaching examples unless I explicitly call them measured results.

1. **First, understand what we were choosing.**

   Imagine four people packing 100 boxes. Someone must decide how to divide the boxes among them.

   One approach gives everyone 25 boxes immediately. Another gives people a few boxes at a time whenever they finish. Another starts with large batches and makes the batches smaller later.

   Those approaches can perform differently. If some boxes take much longer to pack, an equal number of boxes does not mean an equal amount of work.

   In our experiment:

   | Packing example | Computer equivalent |
   |---|---|
   | People doing the packing | Threads running on CPU cores |
   | Individual boxes | Individual loop iterations |
   | Rule for distributing boxes | Scheduling algorithm |
   | Trying different distribution rules | Tuning or searching |
   | Finishing all the boxes | Completing the computation |

   **OpenMP** is the software system that lets a C++ program divide loop iterations among threads.

   We used an existing library called **LB4OMP**, which provides 12 scheduling options. We did not invent those 12 options.

   A scheduler changes **who does which work and when**. The program should still produce the same answer.

2. **The research problem is that choosing a good scheduler also costs time.**

   Suppose there are 12 ways to divide the work.

   You could try all 12 and choose the fastest measured option. But those trials take time and processor effort.

   For a short job, you might spend more time choosing than you save afterward.

   Our approach was:

   > Learn from earlier examples, shortlist a few promising schedulers, test those, and choose one.

   The central method, called **Guided 4**, does this:

   1. Run a basic scheduler called STATIC three times.
   2. Use those measurements and the job’s size to describe the job.
   3. Ask a previously trained model which other schedulers look promising.
   4. Test its top three non-STATIC suggestions, three times each.
   5. Choose the fastest measured option among those three and STATIC.
   6. Keep that choice for the remaining useful executions.

   Therefore, Guided 4 tests **four candidates with three measurements each: 12 test executions**.

   Full search tests **12 candidates with three measurements each: 36 test executions**.

   Guided 4 avoids 24 test executions. Whether that helps overall is what we measured.

   In the paper, a scheduler is sometimes called an **“arm.”** Read that word as **“option.”**

3. **We compared seven ways of making the choice.**

   | Method | Plain-language description | Test executions |
   |---|---|---:|
   | Best fixed | Always use the scheduler that performed best overall on the training examples | 0 |
   | Prior only | Run three basic probes, then trust the model’s prediction | 3 |
   | Guided 2 | Test STATIC and one model suggestion | 6 |
   | Guided 4 | Test STATIC and three model suggestions | 12 |
   | Guided 8 | Test STATIC and seven model suggestions | 24 |
   | Random 4 | Test STATIC and three randomly chosen alternatives | 12 |
   | Full 12 | Test every scheduler | 36 |

   **“Prior” means information learned beforehand.** Here, it means the trained prediction model.

   Notice that “Prior only” still runs three STATIC probes. It avoids testing the predicted winner directly before committing.

   Also, **Full 12 chooses the fastest option in its small set of noisy measurements. That does not guarantee it finds the truly fastest scheduler.**

4. **Equation 1 counts the whole bill.**

   \[
   J_m^{\mathrm{wall}}(H,R)
   =
   \frac{C_{\mathrm{prior}}^{\mathrm{wall}}}{R}
   +
   S_m^{\mathrm{wall}}
   +
   \sum_{t=1}^{H}T_t^{\mathrm{wall}}(a_m)
   \]

   Read it as:

   > **Total time = share of training time + time spent choosing + time spent doing the useful work.**

   Every symbol has a straightforward meaning:

   | Symbol | Meaning |
   |---|---|
   | \(m\) | The selection method, such as Guided 4 |
   | \(a_m\) | The scheduler that method chooses |
   | \(H\) | Number of useful loop executions after choosing |
   | \(R\) | Number of jobs sharing the trained model |
   | \(C_{\mathrm{prior}}\) | Time spent collecting training measurements and fitting the model |
   | \(S_m\) | Time spent choosing a scheduler for this job |
   | \(T_t(a_m)\) | Time taken by useful execution number \(t\) |
   | \(J_m\) | The complete cost we care about |

   The big \(\sum\) means **“add up.”**

   Example:

   - Preparing the model costs 36 seconds.
   - We reuse it across 600 jobs.
   - Each job’s share is \(36/600=0.06\) seconds.
   - Choosing a scheduler takes 0.03 seconds.
   - The useful computation takes 0.20 seconds.

   The total charged to one job is:

   \[
   0.06+0.03+0.20=0.29\text{ seconds}.
   \]

   When the paper reports results with an **“available” or “cached” prior**, it sets aside the already-paid training expense for that comparison. It then examines how much reuse would justify paying that expense.

   The same equation also works for **CPU time**.

   **Wall time** is stopwatch time. **CPU time** adds processor time across the program’s threads. Four threads each consuming one CPU second can produce roughly four CPU seconds during roughly one elapsed second.

   CPU seconds are not electricity measurements.

5. **Equation 2 measures how much execution speed we sacrifice.**

   \[
   \ell_m
   =
   \frac{\widetilde T(a_m)}{\widetilde T^*}-1
   \]

   Read it as:

   > **Slowdown = our execution time divided by the reference execution time, minus one.**

   Here:

   - \(\widetilde T(a_m)\) is the middle measured execution time for our chosen scheduler.
   - \(\widetilde T^*\) is the independently measured best reference time.
   - \(\ell_m\), pronounced “ell,” is the slowdown.

   A tilde, \(\widetilde{\phantom T}\), means we are using a **median**: the middle value after sorting the measurements.

   Example: if the reference takes 10 milliseconds and our choice takes 11:

   \[
   \ell_m=\frac{11}{10}-1=0.10=10\%.
   \]

   Our choice takes 10% more time.

   The second half of Equation 2 expresses the same relationship as **speed retained**:

   \[
   \rho_m
   =
   \frac{\widetilde T^*}{\widetilde T(a_m)}
   =
   \frac{1}{1+\ell_m}.
   \]

   For that example:

   \[
   \rho_m=\frac{10}{11}\approx90.9\%.
   \]

   We retain about 90.9% of the reference speed.

   This distinction matters: **10% more execution time does not mean exactly 10% less speed**, because speed is the inverse of time.

   The paper’s other example is:

   \[
   \frac{1}{1.05}\approx95.24\%.
   \]

   A 5% time penalty retains about 95.24% of the reference speed.

6. **Equation 3 says when the shortcut is worthwhile.**

   \[
   S_F-S_m
   >
   \sum_{t=1}^{H}
   \left[T_t(a_m)-T_t(a_F)\right]
   \]

   Here, \(F\) means Full 12.

   Read it as:

   > **The time saved while choosing must exceed the extra time lost while running.**

   The left side is the choosing-time saving:

   \[
   \text{Full-search choosing time}-\text{our choosing time}.
   \]

   The right side adds up any execution-time penalty afterward.

   Example:

   - Full search spends 100 milliseconds choosing.
   - Our shortcut spends 30 milliseconds choosing.
   - We save 70 milliseconds upfront.
   - Our chosen scheduler takes an extra 0.1 milliseconds per useful execution.

   After 100 useful executions, the penalty is:

   \[
   100\times0.1=10\text{ milliseconds}.
   \]

   We saved 70 milliseconds and lost 10, so we finish 60 milliseconds earlier.

   **This equation assumes the model preparation cost has already been paid.** Otherwise, its share must also be subtracted from the saving.

7. **Equation 4 estimates when a slower choice eventually uses up the upfront saving.**

   First, the paper defines:

   \[
   \Delta T=\bar T(a_m)-\bar T(a_F).
   \]

   The bar means **average**, rather than median.

   \(\Delta T\) is the average extra time our chosen scheduler needs per useful execution.

   If that extra time is positive, the crossover is:

   \[
   H^*=\frac{S_F-S_m}{\Delta T}.
   \]

   Read it as:

   > **Number of executions before the saving disappears = upfront saving divided by extra cost per execution.**

   Using the previous example:

   \[
   H^*=\frac{70\text{ ms}}{0.1\text{ ms per execution}}
   =700\text{ executions}.
   \]

   Before 700, the shortcut wins. At 700, the simplified calculation ties. After 700, full search’s faster chosen scheduler repays its more expensive search.

   This assumes the average execution times stay stable.

   In the measured study, some runs produced an estimated crossover around **935 useful executions**, as the median among the runs where such a crossover existed.

   **935 is not a universal cutoff.** Only 64 of 120 Guided 4 comparisons had both an upfront saving and a positive later execution penalty.

   If our chosen scheduler is equally fast or faster in the measurements, this equation gives no future point where full search catches up under those assumptions.

8. **Equation 5 asks how often we must reuse the model to repay training.**

   \[
   R_{\min}(H)
   =
   \left\lceil
   \frac{C_{\mathrm{prior}}}{d(H)}
   \right\rceil
   \qquad\text{when }d(H)>0.
   \]

   Read it as:

   > **Jobs needed to repay training = training cost divided by average saving per job, rounded upward.**

   Here:

   - \(d(H)\) is the average saving per job with \(H\) useful executions, before charging training.
   - The ceiling brackets \(\lceil\ \rceil\) mean **round up to a whole number**.

   Example: if training costs 36 seconds and each job saves 0.075 seconds:

   \[
   R_{\min}
   =
   \left\lceil\frac{36}{0.075}\right\rceil
   =480.
   \]

   You need approximately 480 such jobs to recover the preparation expense.

   **Measured result:** model preparation cost **35.97 elapsed seconds and 83.89 CPU seconds**.

   For Guided 4 with 50 useful executions per job, the estimated repayment counts were:

   - **488 jobs for elapsed time.**
   - **409 jobs for CPU time.**

   Those are estimates for the workload mixture we tested.

   If each job saves nothing, or costs more, repeating it cannot repay training. That explains the condition \(d(H)>0\).

9. **Before predicting anything, we describe the job using six numbers.**

   The paper writes:

   \[
   x=
   [1,\log_2N,\log_2P,\log_2T_0,L_0,V_0]^\top.
   \]

   Think of \(x\) as a small information card for the job.

   | Entry | What it tells the model |
   |---|---|
   | \(1\) | Allows a scheduler to have a basic starting score |
   | \(\log_2N\) | How large the job is |
   | \(\log_2P\) | How many threads are used |
   | \(\log_2T_0\) | How long the basic STATIC probes took |
   | \(L_0\) | How unevenly the threads finished |
   | \(V_0\) | How spread out their finishing times were |

   The superscript \({}^\top\), called “transpose,” just arranges the list as a column for matrix calculations.

   **Why logarithms?** Job sizes and times can vary by large factors. A logarithm puts multiplication onto a manageable scale.

   For example:

   \[
   \log_2 2=1,\qquad
   \log_2 4=2,\qquad
   \log_2 8=3.
   \]

   Every doubling increases the logged value by one.

   \(L_0\) and \(V_0\) answer related questions: “Did some threads finish much earlier than others?” If so, there may be an opportunity for a different scheduler to distribute work better.

   The code computes imbalance as:

   \[
   L=1-\frac{\text{average thread finish time}}
                    {\text{latest thread finish time}},
   \]

   and variation as:

   \[
   V=
   \frac{\text{standard deviation of thread finish times}}
        {\text{average thread finish time}}.
   \]

   If all threads finish together, both are zero. Larger values indicate more uneven finishing.

   The nonconstant features are also **standardized** using training data: subtract the training average, then divide by the training standard deviation. This prevents features with large numerical values from dominating just because of their units.

10. **Equation 6 turns measured speed into a training score.**

    \[
    r_{i,a}
    =
    \operatorname{clip}
    \left(
    -\frac{\log(T_{i,a}/T_{i,\mathrm{STATIC}})}{\log4},
    -1,1
    \right).
    \]

    This looks intimidating, but it means:

    > **Give a positive score to schedulers faster than STATIC, a negative score to slower ones, and cap extreme scores.**

    The symbols are:

    - \(i\): a training example.
    - \(a\): a scheduler.
    - \(T_{i,a}\): its measured time on that example.
    - \(T_{i,\mathrm{STATIC}}\): STATIC’s measured time.
    - \(r_{i,a}\): the score used to train the predictor.

    Start with the ratio:

    \[
    \frac{T_{i,a}}{T_{i,\mathrm{STATIC}}}.
    \]

    A value below one means faster than STATIC.

    The negative logarithm turns that into a positive score. Dividing by \(\log4\) sets the scale:

    | Performance compared with STATIC | Score |
    |---|---:|
    | Four times faster | \(+1\) |
    | Twice as fast | \(+0.5\) |
    | Same time | \(0\) |
    | Twice as slow | \(-0.5\) |
    | Four times slower | \(-1\) |

    `clip` means **keep the score between −1 and +1**.

    Thus, an extreme measurement cannot create an arbitrarily large training target.

    This “reward” is a numerical label. It is not money, accuracy, or a direct measurement of total time saved.

11. **Equation 7 learns one scoring rule for each scheduler.**

    \[
    A_a
    =
    \lambda I+w\sum_i x_i x_i^\top,
    \qquad
    b_a
    =
    w\sum_i x_i r_{i,a},
    \qquad
    \hat\theta_a=A_a^{-1}b_a.
    \]

    Its purpose is:

    > **Use the training examples to learn which job characteristics predict a good score for each scheduler.**

    This is called **ridge regression**: a weighted-sum predictor with a penalty that discourages excessively large coefficients.

    We learn six coefficients per scheduler, corresponding to the six features.

    To unpack the bookkeeping:

    - \(x_i\) is the description of training example \(i\).
    - \(x_ix_i^\top\) makes a table of all feature-pair products.
    - \(A_a\) combines those products and adds a stabilizing penalty.
    - \(b_a\) connects the features to that scheduler’s observed scores.
    - \(\hat\theta_a\) is the resulting list of learned coefficients.

    \(I\) is the **identity matrix**: ones down the diagonal, zeros elsewhere.

    \(\lambda\) controls the stabilizing penalty. Without it, a model trained on few examples could learn unstable, extreme coefficients.

    \(w\) controls how strongly the training measurements contribute relative to that penalty.

    We used:

    \[
    w=0.25,\qquad\lambda=1.
    \]

    These values were inherited from the earlier study’s training-only validation.

    \(A_a^{-1}\) means the matrix inverse. Its job here is to solve the regression calculation. You do not need to calculate that inverse by hand to explain the study.

    The fitted model is then used through:

    \[
    \text{predicted score for scheduler }a=x^\top\hat\theta_a.
    \]

    That means:

    > **Multiply each feature by its learned coefficient, then add the results.**

    Higher predicted score means the model expects better performance relative to STATIC.

    Crucially, Guided 4 uses those predictions to **shortlist candidates**. Actual timing measurements decide which shortlisted candidate wins.

    Despite the paper’s background discussion of contextual bandits, **this version does not keep learning and switching during useful execution**. It predicts, tests a fixed shortlist, and commits.

12. **Equation 8 constructs the independent comparison reference.**

    \[
    \widetilde T^*_{s,b}
    =
    \min_{a\in\mathcal A}
    \operatorname{median}_{j=1}^{25}
    T^{\mathrm{reference}}_{s,b,a,j}.
    \]

    Read it as:

    > **For each test situation, measure every scheduler independently, find each scheduler’s median time, then take the fastest median.**

    Here:

    - \(s\) means the test scenario.
    - \(b\) means the repetition block.
    - \(\mathcal A\) means the set of 12 schedulers.
    - \(j\) counts the 25 reference executions.
    - `min` means choose the smallest time.

    These measurements were **not supplied to the selection model**. They were used afterward to judge its choice.

    There are therefore two different comparisons:

    | Comparison | Question answered |
    |---|---|
    | Guided 4 versus Full 12 | Does cheaper searching improve the complete process? |
    | Chosen scheduler versus independent reference | How good is the scheduler we ended up with? |

    Why is the reference imperfect? Because timing measurements fluctuate.

    If you measure 12 runners and choose the fastest recorded time, the winner may have benefited from a particularly favorable measurement. Taking the minimum introduces optimism.

    We also checked a second reference method: choose the reference scheduler using other repetition blocks, then measure it in the held-out block. This is **cross-fitting**.

    The results changed considerably under that check. That tells us **the exact “distance from the best” is uncertain**.

13. **The experiments used three types of computation.**

    **Mandelbrot:** calculate pixels of a mathematical image. Some pixels require more work than others, making work distribution important.

    **Triad:** perform simple arithmetic on arrays:

    \[
    a_i=b_i+3c_i.
    \]

    For each position \(i\), multiply the value in array \(c\) by three, add the corresponding value in \(b\), and store it in \(a\).

    **Triangle counting:** count groups of three mutually connected vertices in a graph. Vertices with different numbers of neighbors can require different amounts of work.

    Two other mathematical expressions in the implementation description are simply input-generation rules:

    - \(0.025(\text{seed}\bmod4)\) slightly shifts the Mandelbrot image. “Modulo four” means the remainder after division by four.
    - \(24N\) means the graph generator proposes 24 times as many edges as vertices. Self-connections and duplicate edges are removed, so that is not necessarily the final edge count.

    These are ways to create reproducible test inputs, not learning equations.

    We ran tests with:

    \[
    P\in\{2,4\},
    \]

    meaning **either two or four threads**.

    There were three workload families, four new inputs per family, and two thread counts:

    \[
    3\times4\times2=24\text{ test scenarios}.
    \]

    Each of seven selection methods was measured in five blocks:

    \[
    24\times7\times5=840\text{ primary policy runs}.
    \]

    Test order was shuffled to reduce systematic advantages from running early or late.

    Training used different inputs. The model did not receive the new test measurements as training labels.

14. **The results distinguish choosing-time savings from complete-job savings.**

    Guided 4’s measured choosing costs were approximately:

    - **65.0% less elapsed time.**
    - **65.9% fewer CPU seconds.**

    These percentages concern the **choosing phase**.

    They do not mean that the complete application became 65% faster.

    For the complete comparison, the paper reports:

    \[
    \text{cost ratio}
    =
    \frac{\text{Full 12 total cost}}
         {\text{Guided 4 total cost}}.
    \]

    A ratio above one favors Guided 4.

    With extra tests before useful execution, and an already available model:

    | Useful executions afterward | Full 12 / Guided 4 time ratio | Equivalent elapsed-time saving |
    |---:|---:|---:|
    | 10 | 2.014 | About 50.3% |
    | 50 | 1.379 | About 27.5% |
    | 100 | 1.200 | About 16.7% |
    | 500 | 1.053 | About 5.0% |

    To convert a ratio into a time saving:

    \[
    \text{saving}=1-\frac{1}{\text{ratio}}.
    \]

    At 50 useful executions:

    \[
    1-\frac{1}{1.379}\approx27.5\%.
    \]

    Think of a comparison where full search takes 100 time units: Guided 4 would take about 72.5.

    **Why does the percentage saving shrink for longer jobs?** Choosing is a one-time expense. As useful execution grows, it becomes a smaller part of the whole bill.

15. **The chosen scheduler’s quality requires a more careful explanation.**

    Relative to the independent same-block best reference, Guided 4 had:

    - **10.2% aggregate execution-time penalty.**
    - **90.7% of reference speed retained.**
    - **44.2% of runs within 5% of the reference time.**
    - **64.2% within 10%.**
    - A 90th-percentile penalty of about **31.2%**.

    “90th percentile” means roughly 90% of observations were at or below that penalty; the remaining 10% were worse.

    This means the average result hides some substantial bad cases. We cannot promise a small penalty on every job.

    But relative to **the scheduler actually selected by Full 12**, Guided 4’s additional execution-time penalty was:

    \[
    -1.1\%,
    \]

    with an uncertainty interval from approximately:

    \[
    -3.3\%\text{ to }+0.9\%.
    \]

    A negative penalty means Guided 4 was faster in the estimate. Because the interval includes zero, we should say:

    > **We did not find a clear additional execution-speed penalty compared with the actual full-search procedure.**

    Why can both statements be true?

    Because Full 12’s short search also sometimes picks a scheduler that looks good in its trial measurements but performs less well afterward. Full 12 itself had an 11.4% aggregate penalty against the independent reference.

    **Do not describe Guided 4 as “10.2% slower than exhaustive search.”** The 10.2% is against a different reference.

16. **The statistics describe uncertainty; they do not turn these measurements into a universal promise.**

    The paper combines relative performance using a **geometric mean**.

    For example, if two speed ratios are 2 and 0.5, their geometric mean is:

    \[
    \sqrt{2\times0.5}=1.
    \]

    Doubling performance in one case and halving it in another balance on this multiplicative scale.

    The general calculation is:

    \[
    G=\left(\prod_{i=1}^{n}r_i\right)^{1/n}.
    \]

    Multiply the ratios, then take the \(n\)-th root. This is explanatory notation for the aggregation used in the paper.

    A **95% confidence interval** shows the uncertainty around an estimated effect under the statistical procedure’s assumptions. If a cost-ratio interval includes one, equal cost remains compatible with the measurements.

    We estimated intervals by repeatedly resampling the input configurations 10,000 times.

    The crucial detail is that there were **12 distinct test input configurations**, each measured with two thread counts. Hundreds of thousands of loop measurements are not hundreds of thousands of independent programs.

    Across the full new study, including training, references, and the additional experiment, there were **3,144 processes and 595,896 logged loop executions**. Those counts show substantial measurement work, but they do not establish broad application coverage.

17. **The additional experiment tests the most important catch.**

    Suppose the application needs 50 useful executions.

    If test executions are extra work:

    | Method | Extra tests | Useful executions | Total executions |
    |---|---:|---:|---:|
    | Full 12 | 36 | 50 | 86 |
    | Guided 4 | 12 | 50 | 62 |

    Guided 4 really avoids 24 executions.

    But suppose every test execution already completes part of the required job:

    | Method | Useful executions while testing | Useful executions afterward | Total useful executions |
    |---|---:|---:|---:|
    | Full 12 | 36 | 14 | 50 |
    | Guided 4 | 12 | 38 | 50 |

    Both must still complete 50 useful executions.

    This is what the paper means by:

    \[
    \text{committed executions}=H-n_m,
    \]

    where \(n_m\) is the number of executions spent testing.

    **Testing fewer candidates no longer removes necessary work.** It changes which scheduler performs that work.

    We measured this situation directly:

    - At **50 total useful executions**, Guided 4 was about **3.1% slower** in the point estimate.
    - At **500**, it was essentially tied.
    - We established **no overall time-and-CPU saving** in this operating mode.

    This finding belongs in any honest explanation of the paper.

18. **The simpler alternatives limit what we can claim about machine learning.**

    Randomly testing four candidates also saved substantial time.

    The trained fixed scheduler, which performs no online testing, was also competitive. At 50 useful executions, its complete-time ratio against Full 12 was **1.704**, compared with Guided 4’s **1.379**.

    That does not establish one universal winner, but it does mean:

    > **The results support spending less on search under certain conditions. They do not establish that the learned ranking is necessary to obtain those savings.**

    We also tested only one four-core machine, using small workloads from three families. Training and testing used different inputs from those same families.

    We therefore cannot claim that the method is proven effective on arbitrary applications, other hardware, or large computing clusters.

19. **Here is a presentation-ready explanation you can actually say aloud.**

    > “Our project studies the cost of choosing an OpenMP scheduling algorithm. Different schedulers divide loop iterations among CPU threads differently, and finding a good one requires measurements.
    >
    > “We compared testing all 12 schedulers with using a trained model to shortlist fewer candidates. Our main method tested four candidates, three times each, then committed to the fastest measured choice.
    >
    > “It reduced scheduler-selection time by about 65% and selection CPU time by about 66%. With an existing trained model and 50 useful executions after additional testing, the complete process took about 28% less time.
    >
    > “However, preparing the model had a cost that needed hundreds of reuses to repay. We also found no clear saving when the test executions already counted toward completing the actual job. Simple fixed and random choices were competitive too.
    >
    > “Our contribution is measuring when cheaper selection is worthwhile, including the costs and situations where it does not help.”

    If someone asks **“What did you invent?”**, say:

    > “We implemented and evaluated a budget-limited selection procedure and its cost-versus-quality analysis. We used existing schedulers and an existing regression method.”

    If someone asks **“Did you find the optimal scheduler?”**, say:

    > “We selected a scheduler cheaply and compared it with full search and independent timing references. We did not prove optimality.”

    If someone asks **“Is the trade-off worth it?”**, say:

    > “For the measured workloads, it was worthwhile when testing was additional work and the model preparation cost was already paid or sufficiently reused. We did not demonstrate that benefit when testing already completed useful work.”
