"""
explain_findings.py -- small extra calculations that EXPLAIN the surprising findings (no new simulations of the hedge).

  (1) Why do control variates beat antithetic variates?    -> correlations behind the two variance ratios
  (2) Why is the hedging sd largest near K = 110?          -> the theoretical constant a as a function of K
  (3) Why is the slope not exactly -1/2?                   -> local slopes between neighbouring M values
Run after run_experiments.py.   Writes e5_*.csv, e6_*.csv, local_slopes.csv to ../results/.
"""
import numpy as np, pandas as pd
from scipy.integrate import quad
from mc_pricing import terminal_price, estimate_beta
from asymptotics import asymptotic_constant, second_moment_S2Gamma, discrete_sum_variance
from config import S0, R as r, SIGMA, T, STRIKES, SEED_BIG_SAMPLE, RESULTS_PREFIX as OUT

# ---------------------------------------------------------------- (1) correlations behind variance reduction
Z = np.random.default_rng(SEED_BIG_SAMPLE).standard_normal(5_000_000)  # one big sample (same as the cost table)
ST, STm = terminal_price(Z, S0, r, SIGMA, T), terminal_price(-Z, S0, r, SIGMA, T)
X = np.exp(-r * T) * ST                                           # discounted stock = control variable
vr = pd.read_csv(OUT + "e1_variance_reduction.csv").set_index(["K", "method"])
rows = []
for K in STRIKES:
    Y = np.exp(-r * T) * np.maximum(ST - K, 0)                    # payoff at  Z
    Ym = np.exp(-r * T) * np.maximum(STm - K, 0)                  # payoff at -Z (the antithetic partner)
    rho_xy = np.corrcoef(Y, X)[0, 1]                              # how well the stock predicts the payoff
    rho_anti = np.corrcoef(Y, Ym)[0, 1]                           # correlation inside an antithetic pair
    rows.append(dict(K=K, prob_payoff_zero=np.mean(Y == 0), rho_control=rho_xy, rho_antithetic_pair=rho_anti,
                     predicted_ratio_control=1 / (1 - rho_xy**2), measured_ratio_control=vr.loc[(K, "control"), "variance_ratio"],
                     predicted_ratio_antithetic=1 / (1 + rho_anti), measured_ratio_antithetic=vr.loc[(K, "antithetic"), "variance_ratio"]))
pd.DataFrame(rows).to_csv(OUT + "e5_pricing_explained.csv", index=False)

# ---------------------------------------------------------------- (2) hedging-error constant a as a function of the strike
fwd = S0 * np.exp(r * T)
grid = np.arange(60.0, 161.0, 2.0)
rows = [dict(K=K, sd_constant=np.sqrt(asymptotic_constant(S0, K, r, SIGMA, T)))
        for K in grid]                                            # sqrt(a): sd(HE_M) ~ sqrt(a)/sqrt(M)  (T = 1)
cur = pd.DataFrame(rows)
cur["sd_constant_per_strike"] = cur.sd_constant / cur.K           # same thing measured in units of the strike
cur.to_csv(OUT + "e6_exposure_vs_strike.csv", index=False)

# share of the variance coefficient a that comes from the LAST 10% of the option's life
rows = []
for K in STRIKES:
    f = lambda u: 2 * u * np.exp(-2 * r * (T - u * u)) * second_moment_S2Gamma(T - u * u, S0, K, r, SIGMA, T)
    total = quad(f, 0, np.sqrt(T), limit=200)[0]
    last10 = quad(f, 0, np.sqrt(0.1 * T), limit=200)[0]           # u from 0 to sqrt(0.1 T)  <->  last 10% of time
    rows.append(dict(K=K, share_of_a_from_last_10pct_of_time=last10 / total))
pd.DataFrame(rows).to_csv(OUT + "e6_time_profile.csv", index=False)

# ---------------------------------------------------------------- (3) local slopes between neighbouring M values
d = pd.read_csv(OUT + "e23_hedging.csv")
rows = []
for K in STRIKES:
    g = d[(d.sigma == SIGMA) & (d.K == K) & (d.mu == r)].sort_values("M")
    Ms, sds = g.M.values, g.sd.values
    th = np.array([np.sqrt(discrete_sum_variance(M, S0, K, r, SIGMA, T)) for M in Ms])
    for i in range(len(Ms) - 1):
        rows.append(dict(K=K, M_from=Ms[i], M_to=Ms[i + 1],
                         slope_sim=np.log(sds[i + 1] / sds[i]) / np.log(Ms[i + 1] / Ms[i]),
                         slope_theory_discrete=np.log(th[i + 1] / th[i]) / np.log(Ms[i + 1] / Ms[i])))
pd.DataFrame(rows).to_csv(OUT + "local_slopes.csv", index=False)

pd.set_option("display.width", 200); pd.set_option("display.float_format", lambda x: f"{x:.4f}")
print(pd.read_csv(OUT + "e5_pricing_explained.csv")); print(pd.read_csv(OUT + "e6_time_profile.csv"))
print("peak of sqrt(a):  K =", cur.loc[cur.sd_constant.idxmax(), "K"], "   peak of sqrt(a)/K:  K =", cur.loc[cur.sd_constant_per_strike.idxmax(), "K"], "  forward =", round(fwd, 1))
print(pd.read_csv(OUT + "local_slopes.csv"))
