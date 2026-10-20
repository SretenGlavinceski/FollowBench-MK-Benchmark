# Reads the raw judge replies, repairs formatting problems (logged, decisions never
# changed), compares the two judges and lists every criterion where they differ.
#   python scripts/compare_judges.py

import collections
import csv
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
JUDGING_DIR = os.path.join(ROOT, "judging")
REPLIES_DIR = os.path.join(JUDGING_DIR, "replies")
PARSED_DIR = os.path.join(JUDGING_DIR, "parsed")
QUEUE_FILE = os.path.join(ROOT, "adjudication", "adjudication_queue.csv")

JUDGES = {"A": ("judgeA_chatgpt", "judgeA"), "B": ("judgeB_claude", "judgeB")}
VALID = {"YES", "NO", "UNCERTAIN"}

CURLY_QUOTES = {"\u201c": '"', "\u201d": '"', "\u201e": '"', "\u201f": '"'}
# citation markers ChatGPT inserts into its text; the last one uses private-use characters
CITATION_PATTERNS = [
    re.compile(r"\s*:?chatgpt-content-reference\{[^}]*\}"),
    re.compile(r"\s*:?contentReference\[[^\]]*\](\{[^}]*\})?"),
    re.compile("\\s*\ue200[^\ue201]*\ue201"),
]
FIELD_PATTERN = re.compile(r'"id"\s*:\s*"(C\d+)"\s*,\s*"decision"\s*:\s*"(YES|NO|UNCERTAIN)"'
                           r'(?:\s*,\s*"evidence"\s*:\s*"(.*?)"\s*\})?', re.S)
OBJECT_START = re.compile(r'\{\s*"packet_id"')
PACKET_ID = re.compile(r'\{\s*"packet_id"\s*:\s*"(J\d{4})"')

# recurring disagreements that were decided with one rule each
ADJUDICATION_GROUPS = {
    ("content_002", "C1"): 'P1 Friedman: is "within the rules of the game" required?',
    ("format_020", "C3"): "P2 Title Case: is a correctly capitalised one-word name enough?",
    ("format_007", "C4"): "P3 General statement first: does a section with no examples still pass?",
    ("format_016", "C2"): 'P4 One sentence: does "Label: sentence" count as one sentence?',
}

LOG = []


def log(where, code, message):
    LOG.append([where, code, message])


def clean_text(text, where):
    # R1: curly quotes used as JSON quotes
    n_curly = 0
    for quote in CURLY_QUOTES:
        n_curly += text.count(quote)
    if n_curly:
        for quote, straight in CURLY_QUOTES.items():
            text = text.replace("\\" + quote, '\\"').replace(quote, straight)
        log(where, "R1", "%d curly double quotes converted" % n_curly)
    # R3: citation markers inside the evidence text
    for pattern in CITATION_PATTERNS:
        hits = len(pattern.findall(text))
        if hits:
            text = pattern.sub("", text)
            log(where, "R3", "%d citation marker(s) removed" % hits)
    return text


def split_objects(text):
    starts = [match.start() for match in OBJECT_START.finditer(text)]
    chunks = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(text)
        chunks.append(text[start:end].strip())
    return chunks


def parse_object(chunk):
    decoder = json.JSONDecoder()
    try:
        obj, end = decoder.raw_decode(chunk)
        return obj, "json"
    except json.JSONDecodeError:
        pass
    # R6: not valid JSON, read the fields one by one
    match = PACKET_ID.match(chunk)
    if not match:
        return None, "unreadable"
    decisions = []
    for criterion, decision, evidence in FIELD_PATTERN.findall(chunk):
        decisions.append({"id": criterion, "decision": decision, "evidence": (evidence or "").strip()})
    return {"packet_id": match.group(1), "decisions": decisions}, "fields"


def read_reply(path, expected):
    where = os.path.basename(path)
    raw = open(path, encoding="utf-8").read()
    text = clean_text(raw, where)
    chunks = split_objects(text)

    # R2: several objects on one line, or one object over several lines
    lines = [line for line in raw.splitlines() if line.strip()]
    if chunks and len(lines) != len(chunks):
        log(where, "R2", "%d objects found on %d non-empty lines" % (len(chunks), len(lines)))
    # R4: text around the JSON is ignored
    for line in text.splitlines():
        if line.strip() and not line.lstrip().startswith("{") and '"packet_id"' not in line:
            log(where, "R4", "ignored non-JSON text: " + line.strip()[:120])

    answers = {}
    for i, chunk in enumerate(chunks):
        obj, how = parse_object(chunk)
        if obj is None:
            log(where, "ERROR", "object %d unreadable: %s" % (i + 1, chunk[:80]))
            continue
        if how == "fields":
            log(where, "R6", "%s: read field by field (invalid JSON)" % obj["packet_id"])
        packet_id = obj.get("packet_id")
        # R5: a packet answered twice, the later answer is kept
        if packet_id in answers:
            log(where, "R5", "%s answered twice; later answer used" % packet_id)
        answers[packet_id] = obj

    result = {}
    for item in expected:
        packet_id = item["packet_id"]
        if packet_id not in answers:
            log(where, "MISSING", "%s not answered" % packet_id)
            continue
        found = {}
        for d in answers[packet_id].get("decisions", []):
            decision = str(d.get("decision", "")).strip().upper()
            if decision not in VALID:
                log(where, "ERROR", "%s %s: invalid decision '%s'" % (packet_id, d.get("id"), d.get("decision")))
                continue
            found[d.get("id")] = (decision, str(d.get("evidence", "")).strip())
        for criterion in item["criteria"]:
            if criterion not in found:
                log(where, "MISSING", "%s %s not answered" % (packet_id, criterion))
        extra = set(found) - set(item["criteria"])
        if extra:
            log(where, "ERROR", "%s: unexpected criteria %s" % (packet_id, sorted(extra)))
        result[packet_id] = {}
        for criterion in item["criteria"]:
            if criterion in found:
                result[packet_id][criterion] = found[criterion]
    expected_ids = {item["packet_id"] for item in expected}
    for packet_id in sorted(set(answers) - expected_ids):
        log(where, "ERROR", "%s does not belong to this batch" % packet_id)
    return result


def kappa(pairs):
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    count_a = collections.Counter(a for a, b in pairs)
    count_b = collections.Counter(b for a, b in pairs)
    expected = 0
    for label in set(count_a) | set(count_b):
        expected += count_a[label] * count_b[label]
    expected = expected / (n * n)
    if expected >= 1:
        return 1.0
    return (observed - expected) / (1 - expected)


def write_csv(path, header, rows, encoding="utf-8"):
    with open(path, "w", encoding=encoding, newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def main():
    os.makedirs(PARSED_DIR, exist_ok=True)

    meta = {}
    with open(os.path.join(JUDGING_DIR, "packet_map.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            meta[row["packet_id"]] = row
    packets = {}
    criterion_info = {}
    with open(os.path.join(JUDGING_DIR, "packets.jsonl"), encoding="utf-8") as f:
        for line in f:
            packet = json.loads(line)
            packets[packet["packet_id"]] = packet
            for criterion in packet["criteria"]:
                criterion_info[(packet["packet_id"], criterion["id"])] = (criterion["text"], criterion["lifecycle"])

    decisions = {"A": {}, "B": {}}
    for expected_file in sorted(glob.glob(os.path.join(JUDGING_DIR, "batches", "batch_*_expected.json"))):
        batch = os.path.basename(expected_file).replace("_expected.json", "")
        expected = json.load(open(expected_file))["packets"]
        for judge, (folder, prefix) in JUDGES.items():
            reply_file = os.path.join(REPLIES_DIR, folder, "%s_%s.jsonl" % (prefix, batch))
            if not os.path.exists(reply_file):
                log("%s_%s.jsonl" % (prefix, batch), "MISSING", "reply file not found")
                continue
            for packet_id, found in read_reply(reply_file, expected).items():
                for criterion, value in found.items():
                    decisions[judge][(packet_id, criterion)] = value

    for judge in "AB":
        rows = []
        for (packet_id, criterion), (decision, evidence) in sorted(decisions[judge].items()):
            rows.append([packet_id, criterion, decision, evidence])
        write_csv(os.path.join(PARSED_DIR, "judge%s_decisions.csv" % judge),
                  ["packet_id", "criterion", "decision", "evidence"], rows)

    comparison = []
    for packet_id, criterion in sorted(set(decisions["A"]) | set(decisions["B"])):
        m = meta[packet_id]
        decision_a, evidence_a = decisions["A"].get((packet_id, criterion), ("", ""))
        decision_b, evidence_b = decisions["B"].get((packet_id, criterion), ("", ""))
        text, lifecycle = criterion_info[(packet_id, criterion)]
        if not decision_a or not decision_b:
            status = "missing"
        elif decision_a == decision_b and decision_a != "UNCERTAIN":
            status = "agree"
        elif "UNCERTAIN" in (decision_a, decision_b):
            status = "uncertain"
        else:
            status = "disagree"
        comparison.append({
            "packet_id": packet_id, "criterion": criterion, "item_id": m["item_id"], "pair_id": m["pair_id"],
            "model": m["model"], "lang": m["lang"], "category": m["category"],
            "family_id": m["family_id"], "level": m["level"], "rubric_kind": m["rubric_kind"],
            "partial_equivalence": m["partial_equivalence"], "lifecycle": lifecycle,
            "judge_A": decision_a, "judge_B": decision_b, "status": status,
            "final": decision_a if status == "agree" else "",
            "criterion_text": text, "evidence_A": evidence_a, "evidence_B": evidence_b,
        })
    with open(os.path.join(PARSED_DIR, "comparison.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(comparison[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(comparison)

    queue = []
    for row in comparison:
        if row["status"] == "agree":
            continue
        group = ADJUDICATION_GROUPS.get((row["family_id"], row["criterion"]))
        if group is None and row["category"] == "style":
            group = "C2 Style / persona (subjective)"
        elif group is None:
            group = "C1 Case-by-case (content, accuracy, structure)"
        packet = packets[row["packet_id"]]
        queue.append({
            "group": group, "packet_id": row["packet_id"], "criterion": row["criterion"],
            "family_id": row["family_id"], "level": row["level"], "lang": row["lang"],
            "judge_A_chatgpt": row["judge_A"], "judge_B_claude": row["judge_B"],
            "criterion_text": row["criterion_text"], "evidence_A": row["evidence_A"], "evidence_B": row["evidence_B"],
            "final_decision": "", "adjudicator": "", "reason": "",
            "instruction": packet["instruction"], "response": packet["answer"],
        })
    queue.sort(key=lambda q: (q["group"], q["family_id"], int(q["level"]), q["lang"], q["packet_id"], q["criterion"]))
    with open(QUEUE_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(queue[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(queue)

    write_csv(os.path.join(PARSED_DIR, "parse_log.csv"), ["file", "code", "message"], LOG)

    both = [row for row in comparison if row["judge_A"] and row["judge_B"]]
    report = ["JUDGE COMPARISON",
              "criterion decisions: judge A %d, judge B %d, both %d"
              % (len(decisions["A"]), len(decisions["B"]), len(both))]
    for label, lang in [("all", None), ("en", "en"), ("mk", "mk")]:
        pairs = [(row["judge_A"], row["judge_B"]) for row in both if lang is None or row["lang"] == lang]
        agreement = sum(a == b for a, b in pairs) / len(pairs)
        report.append("agreement %-4s n %4d   %.1f%%   Cohen's kappa %.3f"
                      % (label, len(pairs), 100 * agreement, kappa(pairs)))
    report.append("criteria sent to adjudication: %d" % len(queue))
    codes = collections.Counter(code for where, code, message in LOG)
    report.append("parse log: " + ", ".join("%s %d" % (code, n) for code, n in sorted(codes.items())))
    text = "\n".join(report)
    print(text)
    with open(os.path.join(PARSED_DIR, "agreement_report.txt"), "w", encoding="utf-8") as f:
        f.write(text + "\n")

    if codes["ERROR"] or codes["MISSING"]:
        print("ERROR: the parse log contains ERROR or MISSING entries")
        sys.exit(1)


if __name__ == "__main__":
    main()
