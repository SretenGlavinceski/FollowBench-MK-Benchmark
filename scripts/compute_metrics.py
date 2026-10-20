# HSR, SSR and CSL from the final decisions.
# Analysis A: truncated responses count as failures. Analysis B: they are left out.
#   python scripts/compute_metrics.py

import collections
import csv
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DECISIONS_FILE = os.path.join(ROOT, "results", "final_decisions", "final_decisions_responses.csv")
RESPONSES_FILE = os.path.join(ROOT, "data", "responses", "responses.jsonl")
OUT_DIR = os.path.join(ROOT, "results", "metrics")

MODELS = ["qwen3.5-9b", "gemma-4-12b", "llama-3.1-8b", "domestic-yak-8b"]
LANGS = ["en", "mk"]
CATEGORIES = ["content", "situation", "style", "format"]
LEVELS = [1, 2, 3, 4, 5]
ANALYSES = ["A", "B"]


def mean(values):
    if not values:
        return None
    return sum(values) / len(values)


def fmt(value):
    if value is None:
        return ""
    return round(value, 4)


def write_csv(name, header, rows):
    with open(os.path.join(OUT_DIR, name), "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
    print("wrote results/metrics/" + name)


def load_responses():
    responses = []
    for row in csv.DictReader(open(DECISIONS_FILE, encoding="utf-8")):
        row["level"] = int(row["level"])
        row["truncated"] = row["truncated"] == "True"
        decisions = []
        for i in range(1, 6):
            if row["C%d" % i]:
                decisions.append(row["C%d" % i])
        if row["truncated"]:
            assert not decisions, row["item_id"]
            row["n"] = 0
            row["yes"] = None
            row["hard"] = None
            row["soft"] = None
        else:
            assert len(decisions) == int(row["n_criteria"]), row["item_id"]
            assert len(decisions) in (1, row["level"]), row["item_id"]
            for decision in decisions:
                assert decision in ("YES", "NO"), row["item_id"]
            yes = decisions.count("YES")
            row["n"] = len(decisions)
            row["yes"] = yes
            row["hard"] = int(yes == len(decisions))
            row["soft"] = yes / len(decisions)
        responses.append(row)

    master = {}
    with open(RESPONSES_FILE, encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            master[record["item_id"]] = record
    assert len(responses) == 800 and len(master) == 800
    for row in responses:
        record = master[row["item_id"]]
        assert record["truncated"] == row["truncated"], row["item_id"]
        assert record["model"] == row["model"] and record["lang"] == row["lang"], row["item_id"]
        assert record["family_id"] == row["family_id"] and record["level"] == row["level"], row["item_id"]
    cell_sizes = collections.Counter()
    for row in responses:
        cell_sizes[(row["model"], row["lang"], row["category"], row["level"])] += 1
    assert len(cell_sizes) == 160
    for size in cell_sizes.values():
        assert size == 5
    return responses


def pick(responses, **conditions):
    selected = []
    for row in responses:
        keep = True
        for key, value in conditions.items():
            if row[key] != value:
                keep = False
        if keep:
            selected.append(row)
    return selected


def rates(responses, analysis):
    hard_values = []
    soft_values = []
    for row in responses:
        if row["truncated"]:
            if analysis == "B":
                continue
            hard_values.append(0)
            soft_values.append(0.0)
        else:
            hard_values.append(row["hard"])
            soft_values.append(row["soft"])
    return len(hard_values), mean(hard_values), mean(soft_values)


def family_csl(family_rows, analysis):
    if analysis == "B":
        for row in family_rows:
            if row["truncated"]:
                return None
    by_level = {}
    for row in family_rows:
        by_level[row["level"]] = row
    count = 0
    for level in LEVELS:
        row = by_level[level]
        if row["truncated"] or row["hard"] == 0:
            break
        count += 1
    return count


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    responses = load_responses()
    families = sorted({row["family_id"] for row in responses})
    family_category = {}
    for row in responses:
        family_category[row["family_id"]] = row["category"]

    rows = []
    for r in responses:
        rows.append([r["item_id"], r["model"], r["lang"], r["category"], r["family_id"], r["level"],
                     r["truncated"], r["n"],
                     "" if r["yes"] is None else r["yes"],
                     "" if r["hard"] is None else r["hard"],
                     fmt(r["soft"])])
    write_csv("response_scores.csv",
              ["item_id", "model", "lang", "category", "family_id", "level", "truncated",
               "n_criteria", "n_yes", "hard", "soft"], rows)

    csl = {}
    rows = []
    for model in MODELS:
        for lang in LANGS:
            for family in families:
                family_rows = pick(responses, model=model, lang=lang, family_id=family)
                family_rows.sort(key=lambda row: row["level"])
                csl_a = family_csl(family_rows, "A")
                csl_b = family_csl(family_rows, "B")
                csl[(model, lang, family)] = {"A": csl_a, "B": csl_b}
                chain = ""
                for row in family_rows:
                    chain += "T" if row["truncated"] else str(row["hard"])
                rows.append([model, lang, family_category[family], family, chain, csl_a,
                             "" if csl_b is None else csl_b])
    write_csv("csl_by_family.csv",
              ["model", "lang", "category", "family_id", "levels_L1_to_L5", "csl_A", "csl_B"], rows)

    cell = {}
    rows = []
    for analysis in ANALYSES:
        for model in MODELS:
            for lang in LANGS:
                for category in CATEGORIES:
                    for level in LEVELS:
                        group = pick(responses, model=model, lang=lang, category=category, level=level)
                        n, hsr, ssr = rates(group, analysis)
                        cell[(analysis, model, lang, category, level)] = (hsr, ssr)
                        rows.append([analysis, model, lang, category, level, n, fmt(hsr), fmt(ssr)])
    write_csv("cell_metrics.csv", ["analysis", "model", "lang", "category", "level", "n", "hsr", "ssr"], rows)

    # Analysis A: mean over the 4 categories, as in FollowBench. B: mean over the valid responses.
    level_values = {}
    rows = []
    for analysis in ANALYSES:
        for model in MODELS:
            for lang in LANGS:
                for level in LEVELS:
                    group = pick(responses, model=model, lang=lang, level=level)
                    n, hsr, ssr = rates(group, analysis)
                    if analysis == "A":
                        hsr_per_category = []
                        ssr_per_category = []
                        for category in CATEGORIES:
                            hsr_per_category.append(cell[("A", model, lang, category, level)][0])
                            ssr_per_category.append(cell[("A", model, lang, category, level)][1])
                        hsr_macro = mean(hsr_per_category)
                        ssr_macro = mean(ssr_per_category)
                        assert abs(hsr - hsr_macro) < 1e-9 and abs(ssr - ssr_macro) < 1e-9
                        hsr = hsr_macro
                        ssr = ssr_macro
                    level_values[(analysis, model, lang, level)] = (hsr, ssr)
                    rows.append([analysis, model, lang, level, n, fmt(hsr), fmt(ssr)])
    write_csv("level_metrics.csv", ["analysis", "model", "lang", "level", "n", "hsr", "ssr"], rows)

    category_csl = {}
    rows = []
    for analysis in ANALYSES:
        for model in MODELS:
            for lang in LANGS:
                for category in CATEGORIES:
                    group = pick(responses, model=model, lang=lang, category=category)
                    n, hsr, ssr = rates(group, analysis)
                    if analysis == "A":
                        hsr_per_level = []
                        ssr_per_level = []
                        for level in LEVELS:
                            hsr_per_level.append(cell[("A", model, lang, category, level)][0])
                            ssr_per_level.append(cell[("A", model, lang, category, level)][1])
                        hsr = mean(hsr_per_level)
                        ssr = mean(ssr_per_level)
                    family_values = []
                    for family in families:
                        if family_category[family] != category:
                            continue
                        value = csl[(model, lang, family)][analysis]
                        if value is not None:
                            family_values.append(value)
                    category_csl[(analysis, model, lang, category)] = mean(family_values)
                    rows.append([analysis, model, lang, category, n, fmt(hsr), fmt(ssr),
                                 fmt(mean(family_values)), len(family_values)])
    write_csv("category_metrics.csv",
              ["analysis", "model", "lang", "category", "n", "hsr", "ssr", "csl", "csl_families"], rows)

    rows = []
    for analysis in ANALYSES:
        for model in MODELS:
            for lang in LANGS:
                group = pick(responses, model=model, lang=lang)
                n, hsr, ssr = rates(group, analysis)
                n_truncated = 0
                for row in group:
                    if row["truncated"]:
                        n_truncated += 1
                if analysis == "A":
                    hsr_per_level = []
                    ssr_per_level = []
                    for level in LEVELS:
                        hsr_per_level.append(level_values[("A", model, lang, level)][0])
                        ssr_per_level.append(level_values[("A", model, lang, level)][1])
                    hsr = mean(hsr_per_level)
                    ssr = mean(ssr_per_level)
                    csl_per_category = []
                    for category in CATEGORIES:
                        csl_per_category.append(category_csl[("A", model, lang, category)])
                    total_csl = mean(csl_per_category)
                    n_families = 20
                else:
                    family_values = []
                    for family in families:
                        value = csl[(model, lang, family)]["B"]
                        if value is not None:
                            family_values.append(value)
                    total_csl = mean(family_values)
                    n_families = len(family_values)
                rows.append([analysis, model, lang, n, n_truncated, fmt(hsr), fmt(ssr), fmt(total_csl), n_families])
    write_csv("summary_metrics.csv",
              ["analysis", "model", "lang", "n_responses", "n_truncated", "hsr", "ssr", "csl", "csl_families"], rows)

    rows = []
    for model in MODELS:
        for lang in LANGS:
            for category in CATEGORIES:
                group = pick(responses, model=model, lang=lang, category=category)
                n_truncated = 0
                for row in group:
                    if row["truncated"]:
                        n_truncated += 1
                rows.append([model, lang, category, len(group), n_truncated])
    write_csv("truncation.csv", ["model", "lang", "category", "n", "n_truncated"], rows)


if __name__ == "__main__":
    main()
