# Draws the 5 families per category with seed 42 and checks them against data/prompts.
#   python scripts/select_families.py

import csv
import json
import os
import random

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
POOL_FILE = os.path.join(ROOT, "data", "prompts", "family_pool.csv")
PROMPTS_FILE = os.path.join(ROOT, "data", "prompts", "followbench_en.jsonl")
CATEGORIES = ["content", "situation", "style", "format"]
SEED = 42
PER_CATEGORY = 5


def main():
    pool = {c: [] for c in CATEGORIES}
    with open(POOL_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pool[row["category"]].append(row["family_id"])

    rng = random.Random(SEED)
    selected = []
    for c in CATEGORIES:
        picked = sorted(rng.sample(sorted(pool[c]), PER_CATEGORY))
        print("%-10s %s" % (c, ", ".join(picked)))
        selected += picked

    with open(PROMPTS_FILE, encoding="utf-8") as f:
        in_prompts = sorted({json.loads(line)["family_id"] for line in f if line.strip()})
    if sorted(selected) == in_prompts:
        print("OK: the selected families match data/prompts (%d families)" % len(selected))
    else:
        print("MISMATCH: the selected families differ from data/prompts")


if __name__ == "__main__":
    main()
