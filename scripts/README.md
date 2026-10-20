# Scripts

Run from the repository root, in this order (or all at once with `bash run_all.sh`). Every script works without arguments.

| # | Script | Reads | Writes |
|---|---|---|---|
| 1 | `select_families.py` | `data/prompts/family_pool.csv` | prints the 20 families drawn with seed 42 and checks them against the prompts |
| 2 | `build_responses.py` | `data/prompts/`, `data/responses/raw/` | `data/responses/responses.jsonl` |
| 3 | `build_packets.py` | `responses.jsonl`, `data/criteria/criteria.csv` | `judging/batches/`, `packets.jsonl`, `packet_map.csv`, `packets_report.txt` |
| 4 | `compare_judges.py` | `judging/batches/`, `packets.jsonl`, `judging/replies/` | `judging/parsed/`, `adjudication/adjudication_queue.csv` |
| 5 | `merge_decisions.py` | `comparison.csv`, `adjudication/adjudication_decisions.csv` | `results/final_decisions/` |
| 6 | `compute_metrics.py` | `results/final_decisions/` | `results/metrics/` |
| 7 | `make_tables.py` | `results/metrics/`, `comparison.csv` | `results/tables/`, `docs/RESULTS.md` |
| 8 | `make_figures.py` | `results/metrics/` | `results/figures/` |

Three steps were done by hand, between the scripts:

- **After step 1:** the notebook in `inference/` generated the responses (→ `data/responses/raw/`).
- **After step 3:** each batch was pasted into a new ChatGPT and Claude chat, and the replies were saved unchanged (→ `judging/replies/`).
- **After step 4:** the disagreements were adjudicated (→ `adjudication/adjudication_decisions.csv`).

## Fixed seeds

| Seed | Used for |
|---|---|
| 42 | family selection; generation |
| 2026 | neutral model codes m1–m4 |
| 2027 | shuffling the responses into judge batches |

## Requirements

Python 3.12 or newer. Steps 1–7 use only the standard library; step 8 needs `matplotlib` (`pip install -r requirements.txt`).
