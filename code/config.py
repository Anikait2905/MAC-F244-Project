"""
config.py -- the single place where the project's parameters, seeds and file locations are defined.
Every script imports from here, so changing a number here changes it everywhere, and every script
works no matter which directory it is started from.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS, FIGURES, REPORT = ROOT / "results", ROOT / "figures", ROOT / "report"
# the scripts build file names by string concatenation (OUT + "name.csv"), so also give prefixes ending in "/"
RESULTS_PREFIX, FIGURES_PREFIX, REPORT_PREFIX = (f"{d}/" for d in (RESULTS, FIGURES, REPORT))

S0, R, SIGMA, T = 100.0, 0.05, 0.2, 1.0       # baseline model: spot, interest rate, volatility, maturity
STRIKES = [90.0, 100.0, 110.0]
SIGMAS = [0.1, 0.2, 0.4]                      # volatilities studied in E3 (SIGMA is the baseline one)
MUS = [R, 0.15]                               # real-world drifts: mu = r (risk-neutral case) and mu = 0.15
M_LIST = [4, 12, 26, 52, 126, 252, 504]       # numbers of rebalancing dates
SEED_BIG_SAMPLE = 31                          # 5M-normal sample shared by the cost table and explain_findings.py
