# Data

Everything the models were given and everything they answered.

## `prompts/`

| File | Contents |
|---|---|
| `followbench_en.jsonl` | The 100 English prompts: 20 families × 5 levels, taken from FollowBench |
| `followbench_mk.jsonl` | The same 100 prompts in Macedonian |
| `family_pool.csv` | The FollowBench families the 5 per category were drawn from (seed 42, see `scripts/select_families.py`) |

One prompt per line. The most important fields:

| Field | Meaning |
|---|---|
| `pilot_id` | Family and level, e.g. `format_020_L4`. The same in both languages, so it links an English prompt to its Macedonian counterpart |
| `family_id` | e.g. `format_020` |
| `category_group` | `content`, `situation`, `style` or `format` |
| `level` | 1–5 (level *n* has *n* constraints) |
| `instruction` | The text sent to the model |
| `source`, `example_id`, `category`, `target` | Kept from the original FollowBench record |
| `instruction_en` | (MK only) the English original |
| `translation_status` | (MK only) `draft_mt`: machine translation by GPT-5.6 Sol, not edited |

The Macedonian prompts were translated in batches, each batch in a new chat, level by level, keeping the meaning, the constraints and the structure of the English prompt. The authors read a sample and found it adequate.

## `criteria/criteria.csv`

The checks the judges used, worded exactly as the judges saw them: one row per criterion, 260 rows in total.

| Column | Meaning |
|---|---|
| `category`, `family_id`, `level` | Which prompt the criterion belongs to |
| `criterion` | `C1` … `C5`. A level-*n* prompt has *n* criteria |
| `lifecycle` | How the criterion relates to earlier levels (below) |
| `criterion_en`, `criterion_mk` | The criterion in English and in Macedonian. Each response is checked in its own language |
| `translation_equivalence` | `full`, or `partial` where the English and Macedonian prompts differ slightly |

| `lifecycle` | Meaning |
|---|---|
| `CURRENT_LEVEL_NEW` | The constraint added at this level |
| `CURRENT_LEVEL_RETAINED` | A constraint from an earlier level that still applies |
| `SUPERSEDED_REINTERPRETED` | An earlier constraint that a later level changed (situation_018, L4–L5) |
| `REVISED_ADDENDUM` | An earlier constraint with an added note (format_016, L4) |
| `SINGLE_LEVEL_CRITERION` | Families where each level changes the task (content_019, situation_007, situation_008, style_001): one criterion describing the full expected answer |

The criteria were prepared with the help of an LLM (ChatGPT) and checked by the authors for a subset of families.

## `responses/`

| File | Contents |
|---|---|
| `raw/<model>__<lang>.jsonl` | The notebook output: 100 answers per model and language, exactly as saved during generation |
| `responses.jsonl` | All 800 responses with their prompts, built from `raw/` by `scripts/build_responses.py` |

Fields of `responses.jsonl`:

| Field | Meaning |
|---|---|
| `item_id` | `<pilot_id>__<lang>__<model_code>`, e.g. `format_020_L4__mk__m2` |
| `pair_id` | Links the English and Macedonian response of the same model and prompt |
| `model`, `model_code` | Model name and its neutral code (m1 Qwen3.5 9B, m2 Llama 3.1 8B, m3 Domestic-Yak 8B, m4 Gemma 4 12B) |
| `model_id`, `revision` | Hugging Face identifier and revision |
| `category`, `family_id`, `level`, `pilot_id`, `lang` | Which prompt |
| `instruction`, `instruction_en`, `instruction_sha256` | The prompt text |
| `answer` | The model's response |
| `output_tokens` | Number of generated tokens |
| `status`, `truncated` | `ok` / `truncated`: a truncated response reached the 2,048-token limit and was not judged |
| `source`, `constraint_types`, `translation_status`, `target` | Copied from the prompt |
