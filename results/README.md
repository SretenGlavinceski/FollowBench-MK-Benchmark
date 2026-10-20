# Results

Everything here is produced by the scripts and can be re-created with `bash run_all.sh`.

## The metrics

Each criterion is either satisfied (1) or not (0).

| Metric | Per response | Reported |
|---|---|---|
| **HSR**: Hard Satisfaction Rate | 1 if **all** criteria are satisfied | average over responses |
| **SSR**: Soft Satisfaction Rate | share of criteria satisfied | average over responses |
| **CSL**: Consistent Satisfaction Levels | — | per family, the number of levels in a row from L1 where all criteria are satisfied (0–5), averaged over families |

*Example:* a family passes L1, L2, fails L3 and passes L4 and L5. Its CSL is 2.

As in FollowBench, HSR and SSR are computed for each category and level and then averaged, and CSL is averaged over the families of each category and then over the categories.

**Truncated responses** (95 of 800) were never judged:

- **Analysis A** (main): a truncated response counts as a failure on every criterion and ends its family's CSL chain.
- **Analysis B** (check): truncated responses are left out. CSL uses only families with all five levels valid.

## `final_decisions/`

| File | Contents |
|---|---|
| `final_decisions_criteria.csv` | One row per judged criterion (1,797): both judges, the final decision and whether it came from agreement or adjudication |
| `final_decisions_responses.csv` | One row per response (800): final decisions C1–C5 and the truncated flag |
| `merge_report.txt` | Counts and checks |

## `metrics/`

Values are fractions (0.59 = 59%).

| File | One row per |
|---|---|
| `response_scores.csv` | response: number of criteria, number satisfied, HSR, SSR |
| `csl_by_family.csv` | model × language × family: pass/fail per level and CSL (A and B) |
| `cell_metrics.csv` | model × language × category × level |
| `level_metrics.csv` | model × language × level |
| `category_metrics.csv` | model × language × category |
| `summary_metrics.csv` | model × language |
| `truncation.csv` | model × language × category: truncated responses |

## `tables/`

Numbered as in the paper.

| File | Paper |
|---|---|
| `table05_judge_agreement.csv` | Table 5: judge agreement on the overall verdict |
| `table06_main_results.csv` | Table 6: HSR with 95% Wilson intervals, SSR, CSL |
| `table07_paired_outcomes.csv` | Table 7: prompts satisfied in both, one or neither language |
| `table08_hsr_by_level.csv` | Table 8: HSR by level and CSL |
| `table09_failure_consistency.csv` | Table 9: failure consistency |
| `table10_robustness.csv` | Table 10: final decisions, each judge alone, Analysis B |
| `table12_analysis_b.csv` | Table 12: Analysis B |
| `figure01_truncation_by_model.csv`, `truncation_by_level.csv` | Figure 1 and Section 5.1 |
| `figure04_hsr_by_category.csv` | Figure 4 and Section 5.6 (Analysis A and B) |
| `figure05_ssr_by_level.csv` | Figure 5 |

## `figures/`

| File | Paper |
|---|---|
| `fig1_truncation.png` | Figure 1: truncated responses per model and language |
| `fig2_en_vs_mk.png` | Figure 2: HSR, SSR and CSL, English vs Macedonian |
| `fig3_hsr_by_level.png` | Figure 3: HSR by level |
| `fig4_category_heatmap.png` | Figure 4: HSR per model and category |
| `fig5_ssr_by_level.png` | Figure 5: SSR by level |
| `fig6_analysis_a_vs_b.png` | Figure 6: Analysis A vs B |
