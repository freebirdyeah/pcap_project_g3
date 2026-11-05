# Directory organization

Completed documents and bundles are grouped under `deliverables/`. The current
study is the cost-versus-speed trade-off paper; the previous study examined
warm-started scheduling selection. The original proposal has its own folder.

| Original path | Current path |
| --- | --- |
| `PCAP_TRADEOFF_PAPER_G3.pdf` | `deliverables/current/PCAP_TRADEOFF_PAPER_G3.pdf` |
| `PCAP_TRADEOFF_ARTIFACT_G3.zip` | `deliverables/current/PCAP_TRADEOFF_ARTIFACT_G3.zip` |
| `PCAP_TRADEOFF_SHA256_G3.json` | `deliverables/current/PCAP_TRADEOFF_SHA256_G3.json` |
| `PCAP_RESEARCH_PAPER_G3.pdf` | `deliverables/previous/PCAP_RESEARCH_PAPER_G3.pdf` |
| `PCAP_RESEARCH_ARTIFACT_G3.zip` | `deliverables/previous/PCAP_RESEARCH_ARTIFACT_G3.zip` |
| `ARTIFACT_SHA256.json` | `deliverables/previous/ARTIFACT_SHA256.json` |
| `PCAP_SYNOPSIS_G3.pdf` | `deliverables/proposal/PCAP_SYNOPSIS_G3.pdf` |
| `README.md` | `docs/original-study/README.md` |
| `RESEARCH_LOG.md` | `docs/original-study/RESEARCH_LOG.md` |

The root README is a new guide to both studies. The original README and log
retain their original content. Their reproduction commands assume the project
root as the working directory.

Experiment source, raw data, results, frozen models, and build paths keep their
existing locations. The PDFs beside the LaTeX sources are retained because they
are part of the completed study manifests. The copies under `deliverables/` are
the convenient reading and sharing copies.

The two packaging scripts now put new ZIPs and manifests in `deliverables/`.
Existing ZIPs and checksum manifests retain their original bytes. Their
manifest paths describe the original archived layout, so use the table above
when checking the reorganized workspace. The packaging scripts have intentional
path updates; their current hashes differ from those in the historical bundles.
Historical archives remain independently verifiable without these path changes.

No measurements were rerun and no research results were edited during this
organization.
