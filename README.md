# MAC F244 project – Monte Carlo pricing and delta hedging under GBM

## Run everything
```
pip install numpy scipy matplotlib pandas
cd code
python validate.py            # 33 sanity checks (seconds); exits with status 1 if any fails
python run_experiments.py     # E1-E4, writes ../results/*.csv  (~3 min on 2 cores)
python explain_findings.py    # extra tables explaining the findings (e5_*, e6_*, local_slopes)
python make_figures.py        # writes ../figures/*.png
python build_tables.py        # LaTeX tables/numbers for the report
python extensions.py          # E5 wrong-volatility hedge + E6 real S&P 500 data -> e7_*, e8_* CSVs, fig9, report/numbers_ext.tex
```
Or everything in one go, from any directory: `sh code/run_all.sh` (then `python code/consistency_check.py` is run last).
Dependencies: `pip install -r requirements.txt` (the deck additionally needs `npm install` for `slides/build_deck.js`).
All random numbers use fixed seeds, so results reproduce exactly (CPU timings vary slightly).

## Layout
- `code/bs_utils.py` Black–Scholes price, delta, gamma
- `code/mc_pricing.py` plain / antithetic / control-variate estimators
- `code/hedging.py` exact GBM path recursion + self-financing delta hedge
- `code/asymptotics.py` formulas (11)-(12): closed-form second moment, quadrature, discrete sum
- `code/config.py` the one place for parameters, seeds and paths
- `code/run_experiments.py`, `make_figures.py`, `build_tables.py`, `extensions.py` (E5/E6), `validate.py`
- `data/sp500_fred.csv` S&P 500 daily closes (FRED series SP500, fred.stlouisfed.org/series/SP500), used by E6
- `results/` CSV tables of every experiment, `figures/` PNGs
- `report/` 4-page report (LaTeX source + PDF), `docs/` math notes and viva guide, `slides/` PowerPoint
