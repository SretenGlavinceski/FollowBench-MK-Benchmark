# Judging

Every valid response was judged by two LLM judges, criterion by criterion. The 95 truncated responses were not judged.

## Files

| File | Contents |
|---|---|
| `judge_instructions.txt` | The fixed instructions at the top of every batch |
| `batches/batch_NN.txt` | The 29 batches as pasted into the judge chats (24 or 25 responses each) |
| `batches/batch_NN_expected.json` | The packet and criterion ids each reply had to contain |
| `packets.jsonl` | Every judged response: its opaque id (J0001–J0705), the model, prompt, answer and criteria |
| `packet_map.csv` | Short version: packet id → batch, model, language, category, family, level |
| `packets_report.txt` | Counts for the files above |
| `replies/judgeA_chatgpt/` | Raw replies of Judge A, one file per batch, never edited |
| `replies/judgeB_claude/` | Raw replies of Judge B, one file per batch, never edited |
| `parsed/judgeA_decisions.csv`, `judgeB_decisions.csv` | Each judge's decision and evidence per criterion |
| `parsed/comparison.csv` | Both judges side by side for all 1,797 criteria |
| `parsed/parse_log.csv` | Every formatting repair made while reading the replies |
| `parsed/agreement_report.txt` | Agreement and Cohen's kappa by language, category, model, level and family |

Everything except the replies is produced by `scripts/build_packets.py` and `scripts/compare_judges.py`.

## How the judging was done

- The responses were given opaque ids, shuffled across models and languages (seed 2027) and split into 29 batches. The judges never saw which model wrote a response.
- Both judges received the same batches and instructions. For each criterion they returned YES, NO or UNCERTAIN with a short piece of evidence. UNCERTAIN was never used.
- A new chat was opened for every batch.

| | Judge A | Judge B |
|---|---|---|
| Model | GPT-5.6 Sol (ChatGPT), thinking on | Claude Opus 5.5 (Claude), extended thinking on |
| Chat type | Temporary chat, non-personalised | Incognito chat, outside projects |
| Memory and history | Off | Off; custom instructions cleared |
| Tools | Web search, library and connector search off | Web search, connectors, artifacts, code execution and skills off |

## Reading the replies

The replies were read exactly as returned. Some had formatting problems, which were repaired mechanically and logged in `parse_log.csv`; no decision was changed:

| Code | Repair |
|---|---|
| R1 | Curly quotes used as JSON quotes |
| R2 | Several JSON objects on one line, or one object split over lines |
| R3 | ChatGPT citation markers inside the evidence text |
| R4 | Code fences or extra text around the JSON |
| R5 | A packet answered twice: the judge's last answer is used |
| R6 | A line that is still not valid JSON is read field by field |
