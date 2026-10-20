# FollowBench-MK

**From Rule Selection to Constraint Following: Evaluating Open-Weight LLMs on Macedonian and English Instructions**

Martina Spirovska, Sreten Glavincheski · Faculty of Computer Science and Engineering (FINKI), Ss. Cyril and Methodius University in Skopje · Mentor: Prof. Sonja Gievska

[Paper (PDF)](docs/paper.pdf) · [All results](docs/RESULTS.md)

## About the project

Instruction following means satisfying every requirement in a prompt at the same time: the topic, the format, the tone, the length. This project tests how well open-weight language models do this in English and in Macedonian, a low-resource language.

FollowBench-MK is a paired English–Macedonian subset of [FollowBench](https://github.com/YJiangcm/FollowBench). Each instruction family starts with a simple task, and each of the five levels adds one more constraint. Every English prompt has a Macedonian counterpart, so each model can be compared with itself on the same instruction in both languages.

| | |
|---|---|
| Constraint categories | Content, Situation, Style, Format |
| Instruction families | 20 (5 per category) |
| Levels | 5 (level *n* has *n* constraints) |
| Prompts | 100 per language |
| Models | Qwen3.5 9B, Gemma 4 12B, Llama 3.1 8B, Domestic-Yak 8B |
| Responses | 800 (4 models × 2 languages × 100 prompts) |
| Judges | GPT-5.6 Sol (ChatGPT) and Claude Opus 5.5 (Claude) |

This work follows our earlier project, [RuleTreeBench](https://github.com/SretenGlavinceski/RuleTreeBench-Benchmark), which studied rule selection in a controlled setting.

How it was done:

1. **Prompts.** Five FollowBench families per category were chosen at random (seed 42). The English prompts were machine-translated into Macedonian.
2. **Responses.** Each model answered every prompt once, with greedy decoding, in 4-bit on a Tesla T4 (see the [notebook](inference/)).
3. **Criteria.** Every prompt has a short list of checks (C1 … C*n*), one per constraint, in English and Macedonian.
4. **Judging.** Two LLM judges answered YES or NO for every criterion, without seeing which model wrote the response.
5. **Adjudication.** Where the judges disagreed, the two authors discussed each case and decided.
6. **Metrics.** Hard Satisfaction Rate (HSR), Soft Satisfaction Rate (SSR) and Consistent Satisfaction Levels (CSL), computed as in FollowBench.

## Main results

Analysis A (a truncated response counts as a failure), 100 prompts per model and language.

| Model | Lang | HSR (%) | SSR (%) | CSL |
|---|---|---|---|---|
| Qwen3.5 9B | EN | 59.0 | 77.0 | 2.70 |
| | MK | 51.0 | 67.2 | 2.20 |
| Gemma 4 12B | EN | 60.0 | 74.9 | 2.60 |
| | MK | 50.0 | 64.6 | 2.05 |
| Llama 3.1 8B | EN | 43.0 | 62.5 | 1.75 |
| | MK | 22.0 | 40.2 | 0.95 |
| Domestic-Yak 8B | EN | 7.0 | 21.6 | 0.20 |
| | MK | 8.0 | 17.8 | 0.30 |

![HSR, SSR and CSL per model](results/figures/fig2_en_vs_mk.png)

- The three general-purpose models satisfied all constraints less often in Macedonian. The gap was largest for Llama 3.1 8B.
- The gap was small with one constraint and grew once several constraints had to be met together.
- Style constraints showed the largest language gap.

Every table and figure from the paper is in [docs/RESULTS.md](docs/RESULTS.md).

## Repository structure

```
FollowBench-MK/
├── data/                  prompts, criteria and the 800 model responses
│   ├── prompts/           100 English + 100 Macedonian prompts, and the family pool
│   ├── criteria/          the evaluation criteria (C1 … Cn) in both languages
│   └── responses/         notebook outputs and the combined 800 responses
├── inference/             Colab notebook that generated the responses
├── judging/               batches sent to the judges, their raw replies, parsed decisions
├── adjudication/          the 172 disagreements and their final decisions
├── results/
│   ├── final_decisions/   one final YES/NO per criterion
│   ├── metrics/           HSR, SSR, CSL at every level of detail
│   ├── tables/            the tables of the paper (CSV)
│   └── figures/           the figures of the paper (PNG)
├── scripts/               all Python scripts, in the order they are run
└── docs/                  the paper and the results page
```

The `data`, `inference`, `judging`, `adjudication`, `results` and `scripts` folders each have a README that explains their files.

## Reproducing the results

You need Python 3.12 or newer. The scripts use only the standard library, except the figures, which need `matplotlib`.

```bash
pip install -r requirements.txt
bash run_all.sh
```

`run_all.sh` runs the scripts in this order:

| Step | Script | What it does |
|---|---|---|
| 1 | `select_families.py` | Draws the 20 families with seed 42 and checks they match the prompts |
| 2 | `build_responses.py` | Joins the prompts with the notebook outputs → `data/responses/responses.jsonl` |
| 3 | `build_packets.py` | Builds the blinded, shuffled judge batches |
| 4 | `compare_judges.py` | Reads both judges' replies, compares them, lists the disagreements |
| 5 | `merge_decisions.py` | Combines agreed and adjudicated decisions into the final decisions |
| 6 | `compute_metrics.py` | Computes HSR, SSR and CSL (Analysis A and B) |
| 7 | `make_tables.py` | Writes the paper's tables and `docs/RESULTS.md` |
| 8 | `make_figures.py` | Draws the paper's figures |

Generating the responses (the notebook), judging and adjudication were done by hand; their outputs are included, so every step above can be re-run and gives the same files. See [scripts/README.md](scripts/README.md) for details.

## Models

| Model | Hugging Face |
|---|---|
| Qwen3.5 9B | `Qwen/Qwen3.5-9B` |
| Gemma 4 12B | `google/gemma-4-12B-it` |
| Llama 3.1 8B | `meta-llama/Llama-3.1-8B-Instruct` |
| Domestic-Yak 8B | `LVSTCK/domestic-yak-8B-instruct` |

Settings: 4-bit NF4, greedy decoding, seed 42, up to 2,048 new tokens, one user message with no system prompt, thinking turned off for Qwen and Gemma. The exact revisions are recorded in `data/responses/responses.jsonl`.

## Acknowledgements

The English instructions come from [FollowBench](https://github.com/YJiangcm/FollowBench) (Jiang et al., ACL 2024), released under the Apache-2.0 license. The Macedonian prompts are our machine translations of those instructions.

