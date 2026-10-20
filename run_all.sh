#!/usr/bin/env bash
# Re-runs every scripted step, from the selected families to the figures.
set -e
cd "$(dirname "$0")"

python3 scripts/select_families.py
python3 scripts/build_responses.py
python3 scripts/build_packets.py
python3 scripts/compare_judges.py
python3 scripts/merge_decisions.py
python3 scripts/compute_metrics.py
python3 scripts/make_tables.py
python3 scripts/make_figures.py
