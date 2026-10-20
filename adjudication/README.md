# Adjudication

When both judges gave the same decision on a criterion, that decision is final (1,625 criteria). The other **172 criteria, on 150 responses**, were adjudicated.

## Files

| File | Contents |
|---|---|
| `adjudication_queue.csv` | The 172 disagreements as produced by `scripts/compare_judges.py`, with the decision columns empty |
| `adjudication_decisions.csv` | The same rows with `final_decision`, `adjudicator` and `reason` filled in |

Each row has the instruction, the response, the criterion, both judges' decisions and evidence, but no model name.

## How it was done

The two authors, both native Macedonian speakers, read the instruction, the response and the decisions and evidence of both judges, discussed each case and agreed on the final decision. Every decision has a written reason.

Recurring disagreements were grouped and decided with one rule each:

| Group | Question | Rule | Decisions |
|---|---|---|---|
| P1 | content_002 C1: must Friedman's "within the rules of the game" be stated? | Not required, but profit must be stated as the *sole* duty | 8 YES, 3 NO |
| P2 | format_020 C3: is a correctly capitalised one-word ocean name Title Case? | Yes; whether the name is right is checked by C1 | 6 YES |
| P3 | format_007 C4: does a section without examples still pass? | Yes, if it opens with a general statement | 6 YES |
| P4 | format_016 C2: is "Label: sentence" one sentence? | No, when the label is itself a full sentence | 5 NO |
| C1 | Other content, accuracy and structure criteria | Case by case, consistent with the agreed decisions | 23 YES, 49 NO |
| C2 | Style and persona criteria | Case by case: would a reader recognise the requested voice throughout? | 18 YES, 54 NO |
