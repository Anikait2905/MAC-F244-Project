"""
build_tables.py -- turns the result CSV files into LaTeX tables and number macros, so that every number in the
report and the learning guide is copied from the results (nothing typed by hand).
Output: ../report/tab_pricing.tex, tab_hedging.tex, numbers.tex   (numbers.tex is also used by the guide).
Macro suffixes: A = K 90, B = K 100, C = K 110.
"""
import numpy as np, pandas as pd
from scipy import stats
from config import R as RATE, SIGMA, STRIKES, M_LIST, RESULTS_PREFIX as R, REPORT_PREFIX as OUT
d = pd.read_csv(R + "e23_hedging.csv");        vr = pd.read_csv(R + "e1_variance_reduction.csv")
e1 = pd.read_csv(R + "e1_convergence.csv");    e1b = pd.read_csv(R + "e1_convergence_seed777.csv")
sl = pd.read_csv(R + "e1_slopes.csv");         slb = pd.read_csv(R + "e1_slopes_seed777.csv")
fits = pd.read_csv(R + "e2_slope_fits.csv");   e4 = pd.read_csv(R + "e4_theory_vs_sim.csv")
e4p = pd.read_csv(R + "e4_real_world_drift.csv"); e5 = pd.read_csv(R + "e5_pricing_explained.csv")
cur = pd.read_csv(R + "e6_exposure_vs_strike.csv"); tp = pd.read_csv(R + "e6_time_profile.csv"); ls = pd.read_csv(R + "local_slopes.csv")
SUF = {90.0: "A", 100.0: "B", 110.0: "C"}
mac = {}

# ---------------------------------------------------------------- Table 1: pricing
rows = []
for K in (90.0, 100.0, 110.0):
    c0 = e1[e1.K == K].exact.iloc[0]
    rp = e1[(e1.K == K) & (e1.method == "plain") & (e1.N == 10000)].rmse.iloc[0]
    g = vr[vr.K == K].set_index("method")
    rows.append(f"{K:.0f} & {c0:.3f} & {rp:.3f} & {g.loc['antithetic','variance_ratio']:.1f} & {g.loc['antithetic','cost_adjusted_ratio']:.1f} "
                f"& {g.loc['control','variance_ratio']:.1f} & {g.loc['control','cost_adjusted_ratio']:.1f} \\\\")
    s = SUF[K]
    mac.update({f"vrAnt{s}": f"{g.loc['antithetic','variance_ratio']:.1f}", f"vrCv{s}": f"{g.loc['control','variance_ratio']:.1f}",
                f"caAnt{s}": f"{g.loc['antithetic','cost_adjusted_ratio']:.1f}", f"caCv{s}": f"{g.loc['control','cost_adjusted_ratio']:.1f}",
                f"trAnt{s}": f"{g.loc['antithetic','time_ratio']:.2f}", f"trCv{s}": f"{g.loc['control','time_ratio']:.2f}"})
    e = e5[e5.K == K].iloc[0]
    mac.update({f"rhoCtl{s}": f"{e.rho_control:.2f}", f"rhoAnt{s}": f"{abs(e.rho_antithetic_pair):.2f}", f"pzero{s}": f"{100*e.prob_payoff_zero:.0f}"})
open(OUT + "tab_pricing.tex", "w").write("\n".join(rows))

# ---------------------------------------------------------------- Table 2: hedging error
b = d[d.sigma == SIGMA]
rows = []
for M in M_LIST:
    sd = {K: b[(b.K == K) & (b.mu == RATE) & (b.M == M)].sd.iloc[0] for K in (90.0, 100.0, 110.0)}
    th = e4[(e4.K == 100.0) & (e4.M == M)].sd_discrete_sum.iloc[0]
    q = b[(b.K == 100) & (b.mu == RATE) & (b.M == M)].iloc[0]; p = b[(b.K == 100) & (b.mu == 0.15) & (b.M == M)].iloc[0]
    rows.append(f"{M} & {sd[90.0]:.3f} & {sd[100.0]:.3f} & {th:.3f} & {sd[110.0]:.3f} & ${q['mean']*1e3:+.1f}\\,({q.se_mean*1e3:.1f})$ & ${p['mean']*1e3:+.1f}\\,({p.se_mean*1e3:.1f})$ \\\\")
open(OUT + "tab_hedging.tex", "w").write("\n".join(rows))

# ---------------------------------------------------------------- number macros
dq = d[d.mu == RATE].copy(); dq["z"] = (dq["mean"] / dq.se_mean).abs()
nconf = len(dq); bonf = stats.norm.isf(0.05 / (2 * nconf))
cov2 = lambda m: (e1[e1.method == m].coverage.mean() + e1b[e1b.method == m].coverage.mean()) / 2 * 100
allsl = pd.concat([sl, slb]); F = fits.set_index("K")
mac.update({"nconf": f"{nconf}", "maxz": f"{dq.z.max():.2f}", "bonf": f"{bonf:.2f}",
            "covplain": f"{cov2('plain'):.1f}", "covanti": f"{cov2('antithetic'):.1f}", "covcv": f"{cov2('control'):.1f}",
            "slopeMinAll": f"{allsl.slope.min():.3f}", "slopeMaxAll": f"{allsl.slope.max():.3f}",
            "slopeMinPlain": f"{allsl[allsl.method=='plain'].slope.min():.3f}", "slopeMaxPlain": f"{allsl[allsl.method=='plain'].slope.max():.3f}",
            "slopeSeedOneCvA": f"{sl[(sl.K==90)&(sl.method=='control')].slope.iloc[0]:.3f}",
            "slopeSeedTwoCvA": f"{slb[(slb.K==90)&(slb.method=='control')].slope.iloc[0]:.3f}",
            "ratioDiscMaxHi": f"{e4[e4.M>=126].ratio_sim_over_discrete.max():.3f}", "ratioDiscMinHi": f"{e4[e4.M>=126].ratio_sim_over_discrete.min():.3f}",
            "ratioDiscMfour": f"{e4[e4.M==4].ratio_sim_over_discrete.max():.2f}",
            "ratioLeadMfour": f"{e4[e4.M==4].ratio_sim_over_leading.min():.2f}",
            "ratioPmax": f"{e4p[e4p.M>=12].ratio_P.max():.2f}", "ratioPmin": f"{e4p[e4p.M>=12].ratio_P.min():.2f}"})
for K in (90.0, 100.0, 110.0):
    s = SUF[K]; f = F.loc[K]
    mac.update({f"slopeAll{s}": f"{f.slope_allM:.3f}", f"slopeHi{s}": f"{f.slope_M52plus:.3f}",
                f"slopeHiLo{s}": f"{f.slope_M52plus_lo:.3f}", f"slopeHiHi{s}": f"{f.slope_M52plus_hi:.3f}",
                f"aFit{s}": f"{f.a_fit:.1f}", f"aLo{s}": f"{f.a_lo:.1f}", f"aHi{s}": f"{f.a_hi:.1f}", f"aTh{s}": f"{f.a_theory:.1f}",
                f"bFit{s}": f"{f.b_fit:.1f}"})
    g = b[(b.K == K) & (b.mu == RATE)].set_index("M")
    mac.update({f"relRmseFiftyTwo{s}": f"{100*g.loc[52,'rel_rmse']:.1f}", f"relRmseTwoFiftyTwo{s}": f"{100*g.loc[252,'rel_rmse']:.1f}",
                f"sdFour{s}": f"{g.loc[4,'sd']:.2f}", f"sdFiftyTwo{s}": f"{g.loc[52,'sd']:.3f}", f"sdFiveOhFour{s}": f"{g.loc[504,'sd']:.3f}",
                f"skewFiftyTwo{s}": f"{g.loc[52,'skew']:.2f}", f"kurtFiftyTwo{s}": f"{g.loc[52,'kurt']:.1f}"})
    p = b[(b.K == K) & (b.mu == 0.15)].set_index("M")
    mac[f"sdRatioP{s}"] = f"{(p.loc[[52,126,252,504],'sd']/g.loc[[52,126,252,504],'sd']).mean():.2f}"
    mac[f"sqrtA{s}"] = f"{cur[cur.K==K].sd_constant.iloc[0]:.2f}"
    mac[f"shareLast{s}"] = f"{100*tp[tp.K==K].share_of_a_from_last_10pct_of_time.iloc[0]:.0f}"
mac.update({"peakK": f"{cur.loc[cur.sd_constant.idxmax(),'K']:.0f}", "peakKperK": f"{cur.loc[cur.sd_constant_per_strike.idxmax(),'K']:.0f}",
            "fwd": f"{100*np.exp(RATE):.1f}",
            "lsSimLast": f"{ls[(ls.K==100)&(ls.M_to==504)].slope_sim.iloc[0]:.3f}", "lsThLast": f"{ls[(ls.K==100)&(ls.M_to==504)].slope_theory_discrete.iloc[0]:.3f}",
            "lsThFirst": f"{ls[(ls.K==100)&(ls.M_from==4)].slope_theory_discrete.iloc[0]:.3f}"})
m4 = b[(b.K == 100) & (b.mu == 0.15)].set_index("M")
mac.update({"meanPFour": f"{m4.loc[4,'mean']:.2f}", "meanPTwoFiftyTwo": f"{m4.loc[252,'mean']:.3f}",
            "meanOverSdPct": f"{100*abs(m4.loc[252,'mean'])/m4.loc[252,'sd']:.1f}"})
lo = d[(d.sigma == 0.1) & (d.K == 100) & (d.mu == 0.15) & (d.M <= 126)]
mac.update({"MmeanLow": f"{(lo.M*lo['mean']).max():.2f}", "MmeanHigh": f"{(lo.M*lo['mean']).min():.2f}"})
for sg, nm in [(0.1, "Low"), (0.2, "Mid"), (0.4, "High")]:
    mac[f"sdSig{nm}"] = f"{d[(d.sigma==sg)&(d.K==100)&(d.mu==RATE)&(d.M==252)].sd.iloc[0]:.3f}"
# slope of the THEORETICAL curve (exact sum over t_k) over the same range M >= 52 used for the simulated slope
from asymptotics import discrete_sum_variance
for K in (90.0, 100.0, 110.0):
    Ms = np.array([52, 126, 252, 504])
    th = np.array([0.5 * np.log(discrete_sum_variance(M, 100.0, K, RATE, SIGMA, 1.0)) for M in Ms])
    mac[f"thSlopeHi{SUF[K]}"] = f"{np.polyfit(np.log(Ms), th, 1)[0]:.3f}"
open(OUT + "numbers.tex", "w").write("\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in sorted(mac.items())))
print(len(mac), "macros written")
