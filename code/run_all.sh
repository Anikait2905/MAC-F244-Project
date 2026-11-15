#!/bin/sh
# Runs the whole pipeline from any directory; stops at the first failing step.
set -e
cd "$(dirname "$0")"
python validate.py
python run_experiments.py
python explain_findings.py
python make_figures.py
python build_tables.py
python extensions.py
cd ..
python code/consistency_check.py   # report/guide/deck vs results (run from the project root)
