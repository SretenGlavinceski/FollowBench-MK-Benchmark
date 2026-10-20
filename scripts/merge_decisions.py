# One final decision per criterion: the judges' shared decision where they agree,
# the adjudicated decision where they differ.
#   python scripts/merge_decisions.py

import collections
import csv
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COMPARISON_FILE = os.path.join(ROOT, "judging", "parsed", "comparison.csv")
ADJUDICATED_FILE = os.path.join(ROOT, "adjudication", "adjudication_decisions.csv")
RESPONSES_FILE = os.path.join(ROOT, "data", "responses", "responses.jsonl")
OUT_DIR = os.path.join(ROOT, "results", "final_decisions")


def stop(message):
    print("ERROR:", message)
    sys.exit(1)


def write_csv(name, rows):
    with open(os.path.join(OUT_DIR, name), "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    comparison = list(csv.DictReader(open(COMPARISON_FILE, encoding="utf-8")))
    adjudicated = {}
    for row in csv.DictReader(open(ADJUDICATED_FILE, encoding="utf-8-sig")):
        adjudicated[(row["packet_id"], row["criterion"])] = row
    responses = []
    with open(RESPONSES_FILE, encoding="utf-8") as f:
        for line in f:
            responses.append(json.loads(line))

    if len(comparison) != 1797:
        stop("comparison has %d rows, expected 1797" % len(comparison))
    disagreements = set()
    for row in comparison:
        if row["status"] != "agree":
            disagreements.add((row["packet_id"], row["criterion"]))
    if set(adjudicated) != disagreements:
        stop("the adjudicated criteria are not the same as the disagreements")
    by_key = {(row["packet_id"], row["criterion"]): row for row in comparison}
    for key, row in adjudicated.items():
        if row["final_decision"].strip().upper() not in ("YES", "NO"):
            stop("%s: final_decision '%s' is not YES/NO" % (key, row["final_decision"]))
        original = by_key[key]
        if original["judge_A"] != row["judge_A_chatgpt"] or original["judge_B"] != row["judge_B_claude"]:
            stop("%s: judge decisions differ between the adjudicated file and comparison.csv" % str(key))

    criteria = []
    for row in comparison:
        key = (row["packet_id"], row["criterion"])
        if row["status"] == "agree":
            final = row["judge_A"]
            decided_by = "both_judges"
            group = ""
            adjudicator = ""
            reason = ""
        else:
            decision = adjudicated[key]
            final = decision["final_decision"].strip().upper()
            decided_by = "adjudication"
            group = decision["group"]
            adjudicator = decision["adjudicator"].strip()
            reason = decision["reason"].strip()
        criteria.append({
            "packet_id": row["packet_id"], "item_id": row["item_id"], "pair_id": row["pair_id"],
            "model": row["model"], "lang": row["lang"], "category": row["category"],
            "family_id": row["family_id"], "level": int(row["level"]), "criterion": row["criterion"],
            "rubric_kind": row["rubric_kind"], "lifecycle": row["lifecycle"],
            "partial_equivalence": row["partial_equivalence"],
            "judge_A_chatgpt": row["judge_A"], "judge_B_claude": row["judge_B"],
            "final_decision": final, "decided_by": decided_by, "adjudication_group": group,
            "adjudicator": adjudicator, "adjudication_reason": reason,
            "criterion_text": row["criterion_text"],
        })
    criteria.sort(key=lambda c: (c["category"], c["family_id"], c["level"], c["lang"], c["model"],
                                 int(c["criterion"][1:])))
    write_csv("final_decisions_criteria.csv", criteria)

    decisions_by_item = collections.defaultdict(dict)
    packet_of = {}
    for c in criteria:
        decisions_by_item[c["item_id"]][c["criterion"]] = c["final_decision"]
        packet_of[c["item_id"]] = c["packet_id"]
    rows = []
    for r in responses:
        decisions = decisions_by_item.get(r["item_id"], {})
        if r["truncated"] and decisions:
            stop("truncated response %s has judged decisions" % r["item_id"])
        if not r["truncated"] and not decisions:
            stop("valid response %s has no decisions" % r["item_id"])
        row = {
            "item_id": r["item_id"], "packet_id": packet_of.get(r["item_id"], ""), "pair_id": r["pair_id"],
            "model": r["model"], "model_code": r["model_code"], "lang": r["lang"], "category": r["category"],
            "family_id": r["family_id"], "level": r["level"], "truncated": r["truncated"],
            "judged": bool(decisions), "n_criteria": len(decisions),
        }
        for i in range(1, 6):
            row["C%d" % i] = decisions.get("C%d" % i, "")
        rows.append(row)
    write_csv("final_decisions_responses.csv", rows)

    counts = collections.Counter(c["final_decision"] for c in criteria)
    decided = collections.Counter(c["decided_by"] for c in criteria)
    report = ["FINAL DECISIONS",
              "criterion decisions: %d (YES %d, NO %d)" % (len(criteria), counts["YES"], counts["NO"]),
              "decided by both judges agreeing: %d" % decided["both_judges"],
              "decided by adjudication: %d" % decided["adjudication"],
              "responses: %d judged, %d truncated (not judged)" % (
                  sum(r["judged"] for r in rows), sum(r["truncated"] for r in rows)),
              "all checks passed"]
    text = "\n".join(report)
    print(text)
    with open(os.path.join(OUT_DIR, "merge_report.txt"), "w", encoding="utf-8") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    main()
