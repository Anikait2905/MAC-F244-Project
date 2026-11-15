"""
extensions.py -- two extra experiments added after the first version of the project.

  E5  hedging with a WRONG volatility: the seller prices and hedges with sigma_hat while the stock has sigma = 0.2.
      Theory (asymptotics.mean_wrong_vol): the mean error does not vanish as M grows -- it equals the premium
      mis-pricing C_BS(sigma_hat) - C_BS(sigma) -- while the sd still falls like M^{-1/2}.
  E6  hedging on REAL data: S&P 500 daily closes (FRED series SP500, data/sp500_fred.csv).  A 1-year (250 trading days)
      at-the-money call is sold on every possible start date and delta-hedged with Black-Scholes delta,
      daily (250 steps) or weekly (50 steps), using (i) the trailing 1-year realised volatility known at the start
      (honest) or (ii) the volatility actually realised in the window (hindsight).  Compared with GBM simulation.

Outputs: results/e7_wrong_vol.csv, results/e8_real_data.csv, results/e8_real_data_summary.csv,
         figures/fig9_wrong_vol_and_real_data.png, report/numbers_ext.tex (LaTeX macros for the report).
    python extensions.py        (about 1-2 minutes)
"""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from bs_utils import bs_call, bs_delta
from hedging import simulate_hedge
from asymptotics import mean_wrong_vol
from config import S0, R as r, SIGMA, T, ROOT, RESULTS_PREFIX as RES, FIGURES_PREFIX as FIG, REPORT_PREFIX as REP

mac = {}
K = 100.0

# =============================================================================== E5: wrong volatility
SIG_HAT = [0.10, 0.15, 0.20, 0.25, 0.30]
M_E5 = [52, 252]
N_PATHS = 100_000
rows = []
for sh in SIG_HAT:
    th = mean_wrong_vol(S0, K, r, SIGMA, sh, T)
    for M in M_E5:
        he = simulate_hedge(S0, K, r, SIGMA, T, M, N_PATHS, [r], np.random.default_rng(55 + M), sigma_hedge=sh)[r]
        rows.append(dict(sigma_hat=sh, M=M, mean=he.mean(), se_mean=he.std(ddof=1) / np.sqrt(N_PATHS), sd=he.std(ddof=1),
                         rmse=np.sqrt(np.mean(he**2)), mean_theory=th, premium_gap=bs_call(S0, K, r, sh, T) - bs_call(S0, K, r, SIGMA, T)))
        print(f"E5: sigma_hat={sh}, M={M} done", flush=True)
e5 = pd.DataFrame(rows)
e5.to_csv(RES + "e7_wrong_vol.csv", index=False)
g = e5[(e5.sigma_hat == 0.3)].set_index("M"); g1 = e5[(e5.sigma_hat == 0.1)].set_index("M"); g0 = e5[(e5.sigma_hat == 0.2)].set_index("M")
c0 = bs_call(S0, K, r, SIGMA, T)
mac.update({"wvThHigh": f"{g.loc[252,'mean_theory']:.2f}", "wvSimHigh": f"{g.loc[252,'mean']:.2f}", "wvSimHighFiftyTwo": f"{g.loc[52,'mean']:.2f}",
            "wvThLow": f"{g1.loc[252,'mean_theory']:.2f}", "wvSimLow": f"{g1.loc[252,'mean']:.2f}",
            "wvSdHigh": f"{g.loc[252,'sd']:.2f}", "wvSdHighFiftyTwo": f"{g.loc[52,'sd']:.2f}",
            "wvSdCorrect": f"{g0.loc[252,'sd']:.2f}", "wvSdCorrectFiftyTwo": f"{g0.loc[52,'sd']:.2f}",
            "wvRatioHigh": f"{abs(g.loc[252,'mean'])/g.loc[252,'sd']:.1f}", "wvCzero": f"{c0:.2f}",
            "wvRelHigh": f"{100*g.loc[252,'mean']/c0:.0f}", "wvRelLow": f"{100*abs(g1.loc[252,'mean'])/c0:.0f}",
            })
_w = e5[(e5.M == 252) & (e5.sigma_hat != 0.2)]
mac["wvMaxRelGap"] = f"{100 * ((_w['mean'] - _w.mean_theory).abs() / _w.mean_theory.abs()).max():.1f}"

# =============================================================================== E6: real data (S&P 500)
R_REAL, W = 0.03, 250                                  # assumed risk-free rate; window = 250 trading days (~ 1 year)
raw = pd.read_csv(ROOT / "data" / "sp500_fred.csv")
raw["SP500"] = pd.to_numeric(raw["SP500"], errors="coerce")
raw = raw.dropna().reset_index(drop=True)
P = raw["SP500"].values.astype(float)
dates = pd.to_datetime(raw["observation_date"])
lr = np.diff(np.log(P))                                # daily log returns, lr[j] = ln(P[j+1]/P[j])
ann_vol = lr.std(ddof=1) * np.sqrt(252)
ann_drift = lr.mean() * 252 + 0.5 * ann_vol**2         # mu in dS = mu S dt + sigma S dW
kurt = stats.kurtosis(lr)                              # excess kurtosis (0 for GBM)
skew = stats.skew(lr)
mac.update({"spN": f"{len(P)}", "spStart": dates.iloc[0].strftime("%b %Y"), "spEnd": dates.iloc[-1].strftime("%b %Y"),
            "spVol": f"{100*ann_vol:.1f}", "spDrift": f"{100*ann_drift:.1f}", "spKurt": f"{kurt:.1f}", "spSkew": f"{skew:.2f}"})

starts = np.arange(252, len(P) - W)                    # need one year of history for the trailing volatility
sig_trail = np.array([lr[i - 252:i].std(ddof=1) * np.sqrt(252) for i in starts])
sig_hind = np.array([lr[i:i + W].std(ddof=1) * np.sqrt(252) for i in starts])
T_w = W / 252.0


def hedge_windows(sig, h):
    """Delta-hedge a short ATM 1-year call on every window; rebalance every h trading days; returns HE / C0."""
    steps, dt = W // h, h / 252.0
    S_start = P[starts]; Kw = S_start                  # at-the-money: strike = price at the start date
    C0 = bs_call(S_start, Kw, R_REAL, sig, T_w)
    V = C0.copy()
    for k in range(steps):
        S, Sn = P[starts + k * h], P[starts + (k + 1) * h]
        d = bs_delta(S, Kw, R_REAL, sig, T_w - k * dt)
        V = d * Sn + (V - d * S) * np.exp(R_REAL * dt)
    ST = P[starts + steps * h]
    return np.exp(-R_REAL * T_w) * (V - np.maximum(ST - Kw, 0.0)) / C0


def block_ci(x, stat, B=250, n_boot=1000, seed=3):
    """Moving-block bootstrap 95% interval (windows overlap, so ordinary resampling would be far too optimistic)."""
    rng = np.random.default_rng(seed); n = len(x); nb = int(np.ceil(n / B)); out = []
    for _ in range(n_boot):
        idx = np.concatenate([np.arange(s, s + B) for s in rng.integers(0, n - B, nb)])[:n]
        out.append(stat(x[idx]))
    return np.percentile(out, [2.5, 97.5])


# GBM reference: same volatility as the data (full-sample), same window, same rebalancing, mu = r (so mean ~ 0)
res, out_rows = {}, []
for label, sig in (("trailing", sig_trail), ("hindsight", sig_hind)):
    for name, h in (("daily", 1), ("weekly", 5)):
        he = hedge_windows(sig, h); res[(label, name)] = he
        lo, hi = block_ci(he, np.std)
        mlo, mhi = block_ci(he, np.mean)
        out_rows.append(dict(vol_used=label, rebalancing=name, steps=W // h, n_windows=len(he), mean_rel=he.mean(), mean_lo=mlo, mean_hi=mhi,
                             sd_rel=he.std(ddof=1), sd_lo=lo, sd_hi=hi, rmse_rel=np.sqrt(np.mean(he**2)), skew=stats.skew(he)))
sim = {}
for name, h in (("daily", 1), ("weekly", 5)):
    steps = W // h
    he = simulate_hedge(100.0, 100.0, R_REAL, ann_vol, T_w, steps, 100_000, [R_REAL], np.random.default_rng(88 + h))[R_REAL]
    c0s = bs_call(100.0, 100.0, R_REAL, ann_vol, T_w)
    sim[name] = he / c0s
    out_rows.append(dict(vol_used="GBM simulation", rebalancing=name, steps=steps, n_windows=len(he), mean_rel=sim[name].mean(), mean_lo=np.nan,
                         mean_hi=np.nan, sd_rel=sim[name].std(ddof=1), sd_lo=np.nan, sd_hi=np.nan, rmse_rel=np.sqrt(np.mean(sim[name]**2)),
                         skew=stats.skew(sim[name])))
summ = pd.DataFrame(out_rows); summ.to_csv(RES + "e8_real_data_summary.csv", index=False)
pd.DataFrame({"date": dates.iloc[starts].dt.strftime("%Y-%m-%d").values, "sigma_trailing": sig_trail, "sigma_realised": sig_hind,
              "he_rel_daily_trailing": res[("trailing", "daily")], "he_rel_weekly_trailing": res[("trailing", "weekly")],
              "he_rel_daily_hindsight": res[("hindsight", "daily")], "he_rel_weekly_hindsight": res[("hindsight", "weekly")]}
             ).to_csv(RES + "e8_real_data.csv", index=False)

S = summ.set_index(["vol_used", "rebalancing"])
mac.update({"rwN": f"{len(starts)}",
            "rwSdDailyTrail": f"{100*S.loc[('trailing','daily'),'sd_rel']:.1f}", "rwSdWeeklyTrail": f"{100*S.loc[('trailing','weekly'),'sd_rel']:.1f}",
            "rwSdDailyHind": f"{100*S.loc[('hindsight','daily'),'sd_rel']:.1f}", "rwSdWeeklyHind": f"{100*S.loc[('hindsight','weekly'),'sd_rel']:.1f}",
            "rwSdDailySim": f"{100*S.loc[('GBM simulation','daily'),'sd_rel']:.1f}", "rwSdWeeklySim": f"{100*S.loc[('GBM simulation','weekly'),'sd_rel']:.1f}",
            "rwMeanDailyTrail": f"{100*S.loc[('trailing','daily'),'mean_rel']:+.1f}", "rwMeanWeeklyTrail": f"{100*S.loc[('trailing','weekly'),'mean_rel']:+.1f}",
            "rwMeanDailyHind": f"{100*S.loc[('hindsight','daily'),'mean_rel']:+.1f}",
            "rwMeanLoTrail": f"{100*S.loc[('trailing','daily'),'mean_lo']:+.1f}", "rwMeanHiTrail": f"{100*S.loc[('trailing','daily'),'mean_hi']:+.1f}",
            "rwRatioReal": f"{S.loc[('hindsight','weekly'),'sd_rel']/S.loc[('hindsight','daily'),'sd_rel']:.2f}",
            "rwRatioSim": f"{S.loc[('GBM simulation','weekly'),'sd_rel']/S.loc[('GBM simulation','daily'),'sd_rel']:.2f}",
            "rwRatioTheory": f"{np.sqrt(5):.2f}",
            "rwVolMin": f"{100*sig_trail.min():.0f}", "rwVolMax": f"{100*sig_trail.max():.0f}",
            "rwRatioDailyHindVsTrail": f"{S.loc[('trailing','daily'),'sd_rel']/S.loc[('hindsight','daily'),'sd_rel']:.1f}"})

# =============================================================================== figure
fig, ax = plt.subplots(1, 3, figsize=(11.5, 3.0))
col = {52: "#e8743b", 252: "#1f77b4"}
for M in M_E5:
    d = e5[e5.M == M]
    ax[0].errorbar(d.sigma_hat, d["mean"], yerr=d.sd, fmt="o", color=col[M], capsize=2, ms=4, label=f"simulation, M={M} (bars: ±1 sd)")
xs = np.linspace(0.1, 0.3, 50)
ax[0].plot(xs, [bs_call(S0, K, r, s, T) - c0 for s in xs], "k--", lw=1, label=r"theory $C_{BS}(\hat\sigma)-C_{BS}(\sigma)$")
ax[0].set_xlabel(r"hedging volatility $\hat\sigma$ (true $\sigma$=0.2)"); ax[0].set_ylabel("mean hedging error"); ax[0].set_title("(a) wrong volatility, K=100", fontsize=9)
ax[0].legend(fontsize=6.5, frameon=False)
bins = np.linspace(-0.4, 0.4, 61)
ax[1].hist(res[("hindsight", "daily")], bins=bins, alpha=0.6, color="#1f77b4", label="daily (250 steps)", density=True)
ax[1].hist(res[("hindsight", "weekly")], bins=bins, alpha=0.6, color="#e8743b", label="weekly (50 steps)", density=True)
ax[1].set_xlabel("hedging error / option price"); ax[1].set_title("(b) S&P 500 windows, realised vol used", fontsize=9); ax[1].legend(fontsize=7, frameon=False)
ax[2].plot(dates.iloc[starts].values, 100 * res[("trailing", "daily")], lw=0.7, color="#1f77b4", label="trailing vol")
ax[2].plot(dates.iloc[starts].values, 100 * res[("hindsight", "daily")], lw=0.7, color="#2ca02c", label="hindsight vol")
ax[2].axhline(0, color="k", lw=0.5); ax[2].set_ylabel("error / option price (%)"); ax[2].set_xlabel("start date of the 1-year window")
ax[2].set_title("(c) daily hedge by start date", fontsize=9); ax[2].legend(fontsize=7, frameon=False)
for a in ax: a.tick_params(labelsize=7); a.xaxis.label.set_size(8); a.yaxis.label.set_size(8)
plt.tight_layout(); plt.savefig(FIG + "fig9_wrong_vol_and_real_data.png", dpi=200); plt.close()

with open(REP + "numbers_ext.tex", "w") as f:
    f.write("\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in sorted(mac.items())) + "\n")
print(summ.round(4).to_string()); print(mac)
