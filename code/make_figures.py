"""
make_figures.py -- reads the CSV/NPZ files written by run_experiments.py and draws all figures.
Colours: blue / orange / aqua (colour-blind-checked); marker shape + line style also differ, so colour is never the only cue.
"""
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import RESULTS_PREFIX as RES, FIGURES_PREFIX as FIG, M_LIST
BLUE, ORANGE, AQUA, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#6b6a66"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "grid.linewidth": 0.6, "figure.dpi": 150, "savefig.bbox": "tight",
                     "legend.frameon": False, "axes.titlesize": 9.5})
MET = {"plain": (BLUE, "o", "-"), "antithetic": (ORANGE, "s", "--"), "control": (AQUA, "^", "-.")}
KCOL = {90.0: BLUE, 100.0: ORANGE, 110.0: AQUA}
KMK = {90.0: "o", 100.0: "s", 110.0: "^"}

# ------------------------------------------------------------------ Fig 1: RMSE vs N
e1 = pd.read_csv(RES + "e1_convergence.csv")
sl = pd.read_csv(RES + "e1_slopes.csv")
fig, axes = plt.subplots(1, 3, figsize=(10, 3.1), sharey=True)
for ax, K in zip(axes, [90.0, 100.0, 110.0]):
    for m, (c, mk, ls) in MET.items():
        g = e1[(e1.K == K) & (e1.method == m)]
        s = sl[(sl.K == K) & (sl.method == m)].slope.iloc[0]
        ax.loglog(g.N, g.rmse, color=c, marker=mk, ls=ls, ms=4, lw=1.4, label=f"{m} (slope {s:.3f})")
    g = e1[(e1.K == K) & (e1.method == "plain")]
    ax.loglog(g.N, g.rmse.iloc[0] * (g.N / g.N.iloc[0]) ** -0.5, color=GREY, ls=":", lw=1, label=r"reference $N^{-1/2}$")
    ax.set_title(f"K = {K:.0f}"); ax.set_xlabel("number of payoff evaluations N"); ax.legend(fontsize=7, loc="lower left")
axes[0].set_ylabel("RMSE of price estimate")
fig.savefig(FIG + "fig1_rmse_vs_N.png"); plt.close(fig)

# ------------------------------------------------------------------ Fig 2: sd(HE) vs M, three strikes
d = pd.read_csv(RES + "e23_hedging.csv")
base = d[(d.sigma == 0.2) & (d.mu == 0.05)]
fig, ax = plt.subplots(figsize=(4.6, 3.3))
for K in [90.0, 100.0, 110.0]:
    g = base[base.K == K]
    ax.loglog(g.M, g.sd, color=KCOL[K], marker=KMK[K], ms=4.5, lw=1.4, label=f"K = {K:.0f}")
g = base[base.K == 100.0]
ax.loglog(g.M, g.sd.iloc[0] * (g.M / g.M.iloc[0]) ** -0.5, color=GREY, ls=":", lw=1, label=r"reference $M^{-1/2}$")
ax.set_xlabel("number of rebalancing dates M"); ax.set_ylabel("sd of hedging error"); ax.legend(fontsize=8)
fig.savefig(FIG + "fig2_sd_vs_M.png"); plt.close(fig)

# ------------------------------------------------------------------ Fig 3: histograms of HE (K=100, sigma=0.2, mu=r)
npz = dict(np.load(RES + "baseline_hedging_errors.npz"))   # plain dict: the file is closed straight away
fig, axes = plt.subplots(1, 3, figsize=(10, 2.8))
for ax, M in zip(axes, [12, 52, 252]):
    h = npz[f"Q_M{M}"]
    ax.hist(h, bins=80, color=BLUE, alpha=0.85, density=True)
    xs = np.linspace(h.min(), h.max(), 300)
    ax.plot(xs, np.exp(-0.5 * ((xs - h.mean()) / h.std()) ** 2) / (h.std() * np.sqrt(2 * np.pi)), color=ORANGE, lw=1.4, label="normal, same mean/sd")
    ax.set_title(f"M = {M}:  sd = {h.std():.2f}"); ax.set_xlabel("hedging error"); ax.set_yticks([])
axes[0].legend(fontsize=7)
fig.savefig(FIG + "fig3_histograms.png"); plt.close(fig)

# ------------------------------------------------------------------ Fig 4: sensitivity (strike, volatility, drift)
fig, axes = plt.subplots(1, 3, figsize=(10, 3.1))
ax = axes[0]
for K in [90.0, 100.0, 110.0]:
    g = base[base.K == K]; ax.loglog(g.M, g.rel_rmse, color=KCOL[K], marker=KMK[K], ms=4, lw=1.4, label=f"K = {K:.0f}")
ax.set_title(r"(a) strike: RMSE / $C_0$"); ax.set_xlabel("M"); ax.legend(fontsize=7)
ax = axes[1]
for sg, c, mk in [(0.1, BLUE, "o"), (0.2, ORANGE, "s"), (0.4, AQUA, "^")]:
    g = d[(d.sigma == sg) & (d.K == 100.0) & (d.mu == 0.05)]; ax.loglog(g.M, g.sd, color=c, marker=mk, ms=4, lw=1.4, label=fr"$\sigma$ = {sg}")
ax.set_title("(b) volatility: sd (K = 100)"); ax.set_xlabel("M"); ax.legend(fontsize=7)
ax = axes[2]
for K in [90.0, 100.0, 110.0]:
    q = base[base.K == K].set_index("M").sd
    p = d[(d.sigma == 0.2) & (d.K == K) & (d.mu == 0.15)].set_index("M").sd
    ax.semilogx(M_LIST, (p / q).loc[M_LIST], color=KCOL[K], marker=KMK[K], ms=4, lw=1.4, label=f"K = {K:.0f}")
ax.axhline(1, color=GREY, ls=":", lw=1); ax.set_title(r"(c) drift: sd($\mu$=0.15) / sd($\mu$=r)"); ax.set_xlabel("M"); ax.legend(fontsize=7)
fig.savefig(FIG + "fig4_sensitivity.png"); plt.close(fig)

# ------------------------------------------------------------------ Fig 5: mean of HE under P vs Q
fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.1))
ax = axes[0]
for mu, c, mk, lab in [(0.05, BLUE, "o", r"$\mu = r = 0.05$ (under Q)"), (0.15, ORANGE, "s", r"$\mu = 0.15$ (real world)")]:
    g = d[(d.sigma == 0.2) & (d.K == 100.0) & (d.mu == mu)]
    ax.errorbar(g.M, g["mean"], yerr=2 * g.se_mean, color=c, marker=mk, ms=4, lw=1.3, capsize=2, label=lab)
ax.set_xscale("log"); ax.axhline(0, color=GREY, lw=0.8); ax.set_xlabel("M"); ax.set_ylabel("mean hedging error")
ax.set_title("(a) mean of HE, K = 100, $\\sigma$ = 0.2"); ax.legend(fontsize=7)
ax = axes[1]
for sg, c, mk in [(0.1, BLUE, "o"), (0.2, ORANGE, "s")]:
    g = d[(d.sigma == sg) & (d.K == 100.0) & (d.mu == 0.15)]
    ax.errorbar(g.M, g.M * g["mean"], yerr=2 * g.M * g.se_mean, color=c, marker=mk, ms=4, lw=1.3, capsize=2, label=fr"$\sigma$ = {sg}")
ax.set_xscale("log"); ax.axhline(0, color=GREY, lw=0.8); ax.set_xlabel("M"); ax.set_ylabel("M x mean(HE)")
ax.set_title(r"(b) $\mu$ = 0.15: M $\cdot$ mean $\approx$ constant  $\Rightarrow$ mean = O($\Delta t$)"); ax.legend(fontsize=7)
fig.savefig(FIG + "fig5_drift_mean.png"); plt.close(fig)

# ------------------------------------------------------------------ Fig 6: theory vs simulation (E4)
e4 = pd.read_csv(RES + "e4_theory_vs_sim.csv"); fits = pd.read_csv(RES + "e2_slope_fits.csv")
fig, axes = plt.subplots(1, 3, figsize=(10, 3.1))
ax = axes[0]; g = e4[e4.K == 100.0]
ax.loglog(g.M, g.sd_sim, "o", color=BLUE, ms=5, label="simulation")
ax.loglog(g.M, g.sd_discrete_sum, "-", color=ORANGE, lw=1.5, label="formula (12), sum over $t_k$")
ax.loglog(g.M, g.sd_leading, "--", color=AQUA, lw=1.5, label=r"leading term $\sqrt{a\,\Delta t}$")
ax.set_title("(a) K = 100"); ax.set_xlabel("M"); ax.set_ylabel("sd of hedging error"); ax.legend(fontsize=7)
ax = axes[1]
for K in [90.0, 100.0, 110.0]:
    g = e4[e4.K == K]; ax.semilogx(g.M, g.ratio_sim_over_leading, color=KCOL[K], marker=KMK[K], ms=4, lw=1.4, label=f"K = {K:.0f}")
ax.axhline(1, color=GREY, ls=":", lw=1); ax.set_title("(b) simulated sd / leading-order prediction"); ax.set_xlabel("M"); ax.legend(fontsize=7)
ax = axes[2]
g = base[base.K == 100.0]; dt = 1 / g.M.values; y = g.sd.values ** 2 / dt
f = fits[fits.K == 100.0].iloc[0]
xs = np.linspace(0, dt.max() ** 0.5 * 1.05, 100)
ax.plot(np.sqrt(dt), y, "o", color=BLUE, ms=5, label="simulation")
ax.plot(xs, f.a_fit + f.b_fit * xs, "-", color=ORANGE, lw=1.4, label=r"fit $a + b\sqrt{\Delta t}$")
ax.axhline(f.a_theory, color=AQUA, ls="--", lw=1.4, label=f"theory a = {f.a_theory:.1f}")
ax.set_title(r"(c) Var(HE)/$\Delta t$ against $\sqrt{\Delta t}$"); ax.set_xlabel(r"$\sqrt{\Delta t}$"); ax.legend(fontsize=7)
fig.savefig(FIG + "fig6_theory_vs_sim.png"); plt.close(fig)


# ------------------------------------------------------------------ Fig 7: why K = 110 peaks, and why the slope is not exactly -1/2
cur = pd.read_csv(RES + "e6_exposure_vs_strike.csv"); ls = pd.read_csv(RES + "local_slopes.csv")
fwd = 100 * np.exp(0.05)
fig, axes = plt.subplots(1, 3, figsize=(10, 3.1))
ax = axes[0]
ax.plot(cur.K, cur.sd_constant, color=BLUE, lw=1.6)
for K in [90.0, 100.0, 110.0]:
    ax.plot(K, cur[cur.K == K].sd_constant.iloc[0], KMK[K], color=KCOL[K], ms=6, label=f"K = {K:.0f}")
ax.axvline(100, color=GREY, ls=":", lw=1); ax.axvline(fwd, color=GREY, ls="--", lw=1)
ax.text(98.5, 0.3, "$S_0$", fontsize=7, color=GREY, ha="right"); ax.text(fwd + 1.0, 0.3, "forward", fontsize=7, color=GREY)
ax.set_title(r"(a) $\sqrt{a}$: sd(HE) $\approx\sqrt{a/M}$"); ax.set_xlabel("strike K"); ax.legend(fontsize=7, loc="upper left")
ax = axes[1]
ax.plot(cur.K, cur.sd_constant_per_strike, color=BLUE, lw=1.6)
kb = cur.loc[cur.sd_constant_per_strike.idxmax(), "K"]
ax.plot(kb, cur.sd_constant_per_strike.max(), "o", color=ORANGE, ms=6); ax.text(kb + 3, cur.sd_constant_per_strike.max(), f"peak K = {kb:.0f}", fontsize=7)
ax.axvline(fwd, color=GREY, ls="--", lw=1); ax.set_title(r"(b) same, divided by K"); ax.set_xlabel("strike K")
ax = axes[2]
for K in [90.0, 100.0, 110.0]:
    g = ls[ls.K == K]; xm = np.sqrt(g.M_from * g.M_to)
    ax.semilogx(xm, g.slope_sim, KMK[K], color=KCOL[K], ms=5, ls="none", label=f"simulated, K = {K:.0f}")
g = ls[ls.K == 100.0]; ax.semilogx(np.sqrt(g.M_from * g.M_to), g.slope_theory_discrete, "-", color=GREY, lw=1.3, label="theory (sum over $t_k$), K = 100")
ax.axhline(-0.5, color="black", ls=":", lw=1); ax.set_title("(c) local slope of log sd vs log M"); ax.set_xlabel("M (midpoint of neighbouring pair)"); ax.legend(fontsize=6.5, loc="upper right")
fig.savefig(FIG + "fig7_strike_and_local_slopes.png"); plt.close(fig)

# ------------------------------------------------------------------ Fig 8: why control variates beat antithetic variates
e5 = pd.read_csv(RES + "e5_pricing_explained.csv")
Zs = np.random.default_rng(3).standard_normal(3000)
r_, s_, T_ = 0.05, 0.2, 1.0
STp, STm = 100 * np.exp((r_ - 0.5 * s_**2) * T_ + s_ * Zs), 100 * np.exp((r_ - 0.5 * s_**2) * T_ - s_ * Zs)
fig, axes = plt.subplots(2, 3, figsize=(10, 5.4))
for j, K in enumerate([90.0, 100.0, 110.0]):
    e = e5[e5.K == K].iloc[0]
    Y, Ym = np.exp(-r_ * T_) * np.maximum(STp - K, 0), np.exp(-r_ * T_) * np.maximum(STm - K, 0)
    ax = axes[0, j]; ax.scatter(np.exp(-r_ * T_) * STp, Y, s=4, color=BLUE, alpha=0.5)
    ax.set_title(f"K = {K:.0f}: payoff vs stock, corr = {e.rho_control:.2f}"); ax.set_xlabel("discounted stock price  X")
    if j == 0: ax.set_ylabel("discounted payoff  Y")
    ax = axes[1, j]; ax.scatter(Y, Ym, s=4, color=ORANGE, alpha=0.5)
    ax.set_title(f"K = {K:.0f}: Y(Z) vs Y(-Z), corr = {e.rho_antithetic_pair:.2f}"); ax.set_xlabel("payoff at Z"); ax.set_ylabel("payoff at -Z") if j == 0 else None
fig.tight_layout(); fig.savefig(FIG + "fig8_payoff_scatter.png"); plt.close(fig)
print("figures written")
