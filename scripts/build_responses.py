# Joins the prompts with the notebook outputs into responses.jsonl.
# Each model gets a neutral code (m1-m4) so the judges never see model names.
#   python scripts/build_responses.py

import collections
import glob
import json
import os
import random
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROMPTS_DIR = os.path.join(ROOT, "data", "prompts")
RAW_DIR = os.path.join(ROOT, "data", "responses", "raw")
OUT_FILE = os.path.join(ROOT, "data", "responses", "responses.jsonl")

CATEGORIES = ["content", "situation", "style", "format"]
LEVELS = [1, 2, 3, 4, 5]
LANGS = ["en", "mk"]
CODE_SEED = 2026


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    prompts = {}
    for lang in LANGS:
        prompts[lang] = {r["pilot_id"]: r for r in read_jsonl(os.path.join(PROMPTS_DIR, "followbench_%s.jsonl" % lang))}
    family_category = {r["family_id"]: r["category_group"] for r in prompts["en"].values()}

    answers = {}
    for path in sorted(glob.glob(os.path.join(RAW_DIR, "*.jsonl"))):
        for r in read_jsonl(path):
            answers[(r["model"], r["lang"], r["pilot_id"])] = r
    models = sorted({k[0] for k in answers})

    codes = list(range(1, len(models) + 1))
    random.Random(CODE_SEED).shuffle(codes)
    model_code = {m: "m%d" % c for m, c in zip(models, codes)}

    rows = []
    errors = []
    families = sorted(family_category, key=lambda f: (CATEGORIES.index(family_category[f]), f))
    for fam in families:
        for level in LEVELS:
            pid = "%s_L%d" % (fam, level)
            for lang in LANGS:
                p = prompts[lang].get(pid)
                if p is None:
                    errors.append("missing prompt %s %s" % (lang, pid))
                    continue
                for m in models:
                    r = answers.get((m, lang, pid))
                    if r is None:
                        errors.append("missing response %s %s %s" % (m, lang, pid))
                        continue
                    rows.append({
                        "item_id": "%s__%s__%s" % (pid, lang, model_code[m]),
                        "pair_id": "%s__%s" % (pid, model_code[m]),
                        "category": family_category[fam], "family_id": fam, "level": level, "pilot_id": pid,
                        "lang": lang, "model": m, "model_code": model_code[m],
                        "model_id": r.get("model_id"), "revision": r.get("revision"),
                        "source": p.get("source"),
                        "constraint_types": p.get("category"),
                        "instruction": p["instruction"],
                        "instruction_en": p.get("instruction_en", p["instruction"]),
                        "instruction_sha256": p.get("instruction_sha256"),
                        "translation_status": p.get("translation_status"),
                        "target": p.get("target", ""),
                        "answer": r["answer"],
                        "output_tokens": r["output_tokens"],
                        "status": r["status"],
                        "truncated": r["status"] != "ok",
                    })

    per_cell = collections.Counter((r["model"], r["lang"]) for r in rows)
    if len(rows) != 800 or any(v != 100 for v in per_cell.values()):
        errors.append("expected 100 responses per model and language")
    if errors:
        print("ERRORS:\n  " + "\n  ".join(errors[:20]))
        sys.exit(1)

    with open(OUT_FILE, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("wrote data/responses/responses.jsonl:", len(rows), "responses,",
          sum(r["truncated"] for r in rows), "truncated")
    print("model codes:", ", ".join("%s = %s" % (model_code[m], m) for m in models))


if __name__ == "__main__":
    main()
