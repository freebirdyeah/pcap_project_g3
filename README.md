# Group 3 — OpenMP scheduling research

Start with the **current paper**, which asks whether testing fewer scheduling
methods saves enough time and processor work to be worthwhile.

- [Current paper (PDF)](deliverables/current/PCAP_TRADEOFF_PAPER_G3.pdf)
- [Word-for-word plain-language explanation (PDF)](deliverables/current/PCAP_PAPER_EXPLAINED_G3.pdf)
- [Explanation: standalone LaTeX source](docs/explanation/PCAP_PAPER_EXPLAINED_G3.tex)
- [Results and explanation](tradeoff/RESULTS.md)
- [Current study: code and reproduction guide](tradeoff/README.md)
- [Current study: downloadable artifact](deliverables/current/PCAP_TRADEOFF_ARTIFACT_G3.zip)

Shaan Chopra (240905140), Mrinal Dhami (240905026), and Aniket Verma (240905156).

## Where things are

| Location | Contents |
| --- | --- |
| `deliverables/current/` | Latest paper, full experiment ZIP, and its checksum manifest |
| `deliverables/previous/` | Earlier paper, experiment ZIP, and its checksum manifest |
| `deliverables/proposal/` | Original project synopsis |
| `tradeoff/` | Current study: experiment scripts, raw data, results, and LaTeX source |
| `paper/` | Earlier study: LaTeX source, figures, and generated PDF |
| `src/`, `scripts/`, `tests/` | Shared implementation and earlier experiment tools |
| `data/`, `results/` | Earlier study: raw measurements and analyzed results |
| `docs/original-study/` | Earlier reproduction guide and research log |
| `build/` | Compiled programs and runtime build files |
| `vendor/`, `patches/` | External OpenMP runtime and its portability patch |
| `requirements.txt` | Python dependencies |

The current manuscript source is
[`tradeoff/paper/PCAP_TRADEOFF_PAPER_G3.tex`](tradeoff/paper/PCAP_TRADEOFF_PAPER_G3.tex).
The earlier source is
[`paper/PCAP_RESEARCH_PAPER_G3.tex`](paper/PCAP_RESEARCH_PAPER_G3.tex).

## Results in plain language

Testing four methods instead of twelve reduced the time spent choosing by about
65% and the processor time spent choosing by about 66%. For short jobs with 50
useful executions, choosing and doing the job together took about 28% less time
when the previously trained model was available.

Preparing that model has a cost, so this makes sense when it is reused many
times. When the test executions themselves completed useful work, testing fewer
methods did not produce a clear overall saving. See the current paper for the
measurements and their limits.

## Working with the project

Run build and experiment commands from this directory. Follow the
[current guide](tradeoff/README.md) or the
[earlier guide](docs/original-study/README.md) for the relevant study.

The packaging commands now write to the corresponding deliverables folders:

```bash
python3 tradeoff/package.py
python3 scripts/package.py
```

These commands replace the corresponding ZIP and checksum manifest; run them
only when intentionally producing a new bundle. Existing ZIPs are preserved
snapshots of the completed studies. See
[the organization note](docs/ORGANIZATION.md) for moved paths and checksum details.
