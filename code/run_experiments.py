"""
run_experiments.py -- runs Experiments 1-4 and saves the numerical tables as CSV files in ../results/.

    python run_experiments.py            # all experiments (about 3-4 minutes)
    python run_experiments.py e1 e23 e4  # or only some of them

  E1  : Monte Carlo pricing error versus the number of samples N          (Part A)
  E2/3: hedging error versus rebalancing dates M, strikes, volatilities, drifts   (Part B)
  E4  : comparison of the simulated hedging error with the theoretical formula    (Part B)
Figures are drawn separately by make_figures.py.
"""
import sys, time
import numpy as np, pandas as pd
from scipy import stats
from bs_utils import bs_call
from mc_pricing import mc_plain, mc_antithetic, mc_control_variate, estimate_beta, terminal_price
from hedging import simulate_hedge
from asymptotics import asymptotic_constant, discrete_sum_variance
from config import (S0, R as r, SIGMA, T, STRIKES, SIGMAS, MUS, M_LIST, SEED_BIG_SAMPLE,
                    RESULTS_PREFIX as OUT)

# ----------------------------------------------------------------- baseline parameters: see config.py

# ----------------------------------------------------------------- experiment settings
N_LEVELS = [int(2 * round(10 ** x / 2)) for x in np.linspace(2, 6, 9)]   # 100 ... 1,000,000 (9 log-spaced, even numbers)
R_REPS   = 400                    # replications per N (the proposal said 1000; reduced to keep the run time short)
N_PATHS  = 100_000                # hedged paths per (strike, volatility, M)
N_BOOT   = 500                    # bootstrap resamples for confidence intervals


# =============================================================================== Experiment 1
def cost_comparison(methods, betas, df):
    """
    Variance reduction ratios and CPU cost for each strike.
      variance_ratio       = (variance of plain MC) / (variance of the method), same number of payoff evaluations,
                             measured on ONE big sample of 5 million normals (precise)
      variance_ratio_sample= the same ratio estimated from the replications in df (a cross-check)
      time_ratio           = CPU time of the method / CPU time of plain MC  (N = 1,000,000, best of 15 runs)
      cost_adjusted_ratio  = variance_ratio / time_ratio   (the gain after paying for the extra work)
    """
    Nt = 1_000_000
    draws = {"plain": Nt, "antithetic": Nt // 2, "control": Nt}      # normals each method needs for N = 1e6 payoffs
    rows = []
    # --- one big sample (K-independent), drawn once and reused for every strike
    Zb = np.random.default_rng(SEED_BIG_SAMPLE).standard_normal(5_000_000)
    ST = terminal_price(Zb, S0, r, SIGMA, T)
    STm = terminal_price(-Zb, S0, r, SIGMA, T)
    X = np.exp(-r * T) * ST
    for K in STRIKES:
        # --- CPU time: each method draws its own random numbers and computes its estimate
        tm = {}
        for m, f in methods.items():
            best = 1e9
            for _ in range(15):
                t0 = time.perf_counter()
                f(np.random.default_rng(1).standard_normal(draws[m]), K)
                best = min(best, time.perf_counter() - t0)
            tm[m] = best
        # --- precise variances per payoff budget, from one big sample
        Y = np.exp(-r * T) * np.maximum(ST - K, 0)
        Yminus = np.exp(-r * T) * np.maximum(STm - K, 0)
        var = {"plain": Y.var(ddof=1),
               "antithetic": 2 * (0.5 * (Y + Yminus)).var(ddof=1),    # per payoff evaluation (a pair uses 2)
               "control": (Y - betas[K] * (X - S0)).var(ddof=1)}
        # --- cross-check from the replications: N * RMSE^2 estimates the same quantity
        g = df[(df.K == K) & (df.N >= 10**5)]
        v_rep = {m: np.mean(g[g.method == m].N.values * g[g.method == m].rmse.values**2) for m in methods}
        for m in methods:
            rows.append(dict(K=K, method=m, variance_ratio_sample=v_rep["plain"] / v_rep[m],
                             variance_ratio=var["plain"] / var[m], time_s=tm[m], time_ratio=tm[m] / tm["plain"],
                             cost_adjusted_ratio=(var["plain"] / var[m]) / (tm[m] / tm["plain"])))
    return pd.DataFrame(rows)


def experiment1(seed=2026, tag="", with_cost=True):
    """
    Question: how fast does the Monte Carlo price converge to Black-Scholes as N grows, and do antithetic /
    control variates help?  We repeat each estimate R_REPS times for every N and measure:
        bias, RMSE (error relative to the exact BS price), mean SE, and the coverage of the 95% CI.
    """
    rng = np.random.default_rng(seed)
    assert all(N % 2 == 0 for N in N_LEVELS), "antithetic variates need an even number of payoff evaluations"
    betas = {K: estimate_beta(S0, K, r, SIGMA, T) for K in STRIKES}
    exact = {K: bs_call(S0, K, r, SIGMA, T) for K in STRIKES}
    methods = {"plain":      lambda Z, K: mc_plain(Z, S0, K, r, SIGMA, T),
               "antithetic": lambda Z, K: mc_antithetic(Z[: len(Z) // 2], S0, K, r, SIGMA, T),   # uses N/2 normals
               "control":    lambda Z, K: mc_control_variate(Z, S0, K, r, SIGMA, T, betas[K])}
    rows = []
    for N in N_LEVELS:
        est = {(m, K): np.empty(R_REPS) for m in methods for K in STRIKES}
        se  = {(m, K): np.empty(R_REPS) for m in methods for K in STRIKES}
        disc = np.exp(-r * T)
        for rep in range(R_REPS):
            Z = rng.standard_normal(N)          # the same N random numbers feed all methods and strikes
            ST = terminal_price(Z, S0, r, SIGMA, T)                 # computed once, shared by all methods and strikes
            STm = terminal_price(-Z[: N // 2], S0, r, SIGMA, T)     # antithetic partners of the first N/2 normals
            X = disc * ST
            for K in STRIKES:
                Y = disc * np.maximum(ST - K, 0.0)                                              # plain payoffs
                W = 0.5 * (disc * np.maximum(ST[: N // 2] - K, 0.0) + disc * np.maximum(STm - K, 0.0))  # pair averages
                A = Y - betas[K] * (X - S0)                                                     # control-variate payoffs
                for m, v in (("plain", Y), ("antithetic", W), ("control", A)):
                    est[m, K][rep], se[m, K][rep] = v.mean(), v.std(ddof=1) / np.sqrt(len(v))
        for (m, K), e in est.items():
            err = e - exact[K]                  # error of each replication
            rows.append(dict(K=K, N=N, method=m, bias=err.mean(), rmse=np.sqrt(np.mean(err**2)),
                             mean_se=se[m, K].mean(), coverage=np.mean(np.abs(err) <= 1.96 * se[m, K]),
                             exact=exact[K]))
        print("E1: N =", N, flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT + f"e1_convergence{tag}.csv", index=False)

    # slope of log(RMSE) against log(N): theory says -1/2.  (OLS line with a 95% confidence interval)
    srows = []
    for (K, m), g in df.groupby(["K", "method"]):
        x, y = np.log(g.N.values), np.log(g.rmse.values)
        fit = stats.linregress(x, y)
        tcrit = stats.t.ppf(0.975, len(x) - 2)
        srows.append(dict(K=K, method=m, slope=fit.slope, ci_lo=fit.slope - tcrit * fit.stderr,
                          ci_hi=fit.slope + tcrit * fit.stderr, intercept=fit.intercept))
    pd.DataFrame(srows).to_csv(OUT + f"e1_slopes{tag}.csv", index=False)
    if with_cost:
        cost_comparison(methods, betas, df).to_csv(OUT + "e1_variance_reduction.csv", index=False)


# =============================================================================== Experiments 2 and 3
def bootstrap_fit(HE_by_M, Ms, rng, min_M=52):
    """
    Fits the straight lines used to test the M^(-1/2) law and gives 95% bootstrap confidence intervals.
      slope_allM / slope_M52plus : slope of log(sd) against log(M), using all M / only M >= 52
      a, b : Var(HE) / dt = a + b*sqrt(dt)    (a = leading constant, b = size of the finite-M correction)
    Bootstrap: resample the simulated paths with replacement, recompute every sd, refit; repeat N_BOOT times.
    The 2.5% and 97.5% percentiles of the refitted numbers form the 95% interval.
    Returns (point estimates, lower limits, upper limits), each = (slope_all, slope_52plus, a, b).
    """
    Ms = np.array(Ms)
    dts = T / Ms

    def fit(sds):
        slope_all = np.polyfit(np.log(Ms), np.log(sds), 1)[0]
        big = Ms >= min_M
        slope_hi = np.polyfit(np.log(Ms[big]), np.log(sds[big]), 1)[0]
        b, a = np.polyfit(np.sqrt(dts), sds**2 / dts, 1)          # straight line: intercept a, slope b
        return slope_all, slope_hi, a, b

    point = fit(np.array([HE_by_M[M].std(ddof=1) for M in Ms]))
    n = len(HE_by_M[Ms[0]])
    boots = []
    for _ in range(N_BOOT):
        sds = np.array([HE_by_M[M][rng.integers(0, n, n)].std(ddof=1) for M in Ms])
        boots.append(fit(sds))
    lo, hi = np.percentile(np.array(boots), [2.5, 97.5], axis=0)
    return point, lo, hi


def experiment23():
    """
    Question (E2): how does the hedging error change with the number of rebalancing dates M?
    Question (E3): how does it depend on strike K, volatility sigma and real-world drift mu?
    For every (sigma, K, M) we hedge N_PATHS random paths under both drifts and record the statistics of HE_M.
    For sigma = 0.2, mu = r we also fit the M^(-1/2) law (bootstrap CIs) and compare with theory.
    """
    rng = np.random.default_rng(99)
    rows, fits = [], []
    for sigma in SIGMAS:
        for K in STRIKES:
            C0 = bs_call(S0, K, r, sigma, T)
            HE = {mu: {} for mu in MUS}                       # HE[mu][M] = array of hedging errors
            for M in M_LIST:
                out = simulate_hedge(S0, K, r, sigma, T, M, N_PATHS, MUS, rng)
                for mu in MUS:
                    h = out[mu]
                    HE[mu][M] = h
                    q5, q95 = np.percentile(h, [5, 95])
                    rows.append(dict(sigma=sigma, K=K, mu=mu, M=M, C0=C0, mean=h.mean(),
                                     se_mean=h.std(ddof=1) / np.sqrt(len(h)), sd=h.std(ddof=1),
                                     rmse=np.sqrt(np.mean(h**2)), rel_rmse=np.sqrt(np.mean(h**2)) / C0,
                                     q05=q5, q95=q95, skew=stats.skew(h), kurt=stats.kurtosis(h)))
            if sigma == SIGMA:                               # baseline volatility, mu = r
                (sl_all, sl_hi, a, b), lo, hi = bootstrap_fit(HE[r], M_LIST, rng)
                fits.append(dict(K=K, slope_allM=sl_all, slope_allM_lo=lo[0], slope_allM_hi=hi[0],
                                 slope_M52plus=sl_hi, slope_M52plus_lo=lo[1], slope_M52plus_hi=hi[1],
                                 a_fit=a, a_lo=lo[2], a_hi=hi[2], b_fit=b,
                                 a_theory=asymptotic_constant(S0, K, r, sigma, T)))
            print(f"E2/E3: sigma={sigma}, K={K} done", flush=True)
    pd.DataFrame(rows).to_csv(OUT + "e23_hedging.csv", index=False)
    pd.DataFrame(fits).to_csv(OUT + "e2_slope_fits.csv", index=False)
    # raw hedging errors for the baseline case (K=100, sigma=0.2, mu=r), used only for the histograms
    hq = {f"Q_M{M}": simulate_hedge(S0, 100.0, r, SIGMA, T, M, N_PATHS, [r], np.random.default_rng(5 + M))[r]
          for M in (12, 52, 252)}
    np.savez_compressed(OUT + "baseline_hedging_errors.npz", **hq)


# =============================================================================== Experiment 4
def experiment4():
    """
    Question: does the theoretical formula for Var(HE_M) predict the simulated standard deviation?
    Compares, for each K and M:  simulated sd   |   leading term sqrt(a*dt)   |   exact sum over the dates t_k.
    Second table: the same comparison for real-world drift mu = 0.15 (expectation taken under that drift).
    """
    df = pd.read_csv(OUT + "e23_hedging.csv")
    pick = lambda K, mu, M: df[(df.sigma == SIGMA) & (df.K == K) & (df.mu == mu) & (df.M == M)].iloc[0]
    rows, rows_p = [], []
    for K in STRIKES:
        a_th = asymptotic_constant(S0, K, r, SIGMA, T)
        for M in M_LIST:
            sim = pick(K, r, M)
            lead = np.sqrt(a_th * T / M)
            disc = np.sqrt(discrete_sum_variance(M, S0, K, r, SIGMA, T))
            rows.append(dict(K=K, M=M, sd_sim=sim.sd, sd_leading=lead, sd_discrete_sum=disc,
                             ratio_sim_over_leading=sim.sd / lead, ratio_sim_over_discrete=sim.sd / disc))
            simp = pick(K, 0.15, M)
            pred_p = np.sqrt(discrete_sum_variance(M, S0, K, r, SIGMA, T, mu=0.15))
            rows_p.append(dict(K=K, M=M, sd_sim_P=simp.sd, sd_pred_P=pred_p, sd_sim_Q=sim.sd, sd_pred_Q=disc,
                               ratio_P=simp.sd / pred_p, ratio_Q=sim.sd / disc))
    pd.DataFrame(rows).to_csv(OUT + "e4_theory_vs_sim.csv", index=False)
    pd.DataFrame(rows_p).to_csv(OUT + "e4_real_world_drift.csv", index=False)


def rerun_cost_only():
    """Recomputes only the variance-reduction/CPU-cost table (uses the saved E1 results)."""
    betas = {K: estimate_beta(S0, K, r, SIGMA, T) for K in STRIKES}
    methods = {"plain":      lambda Z, K: mc_plain(Z, S0, K, r, SIGMA, T),
               "antithetic": lambda Z, K: mc_antithetic(Z[: len(Z) // 2], S0, K, r, SIGMA, T),
               "control":    lambda Z, K: mc_control_variate(Z, S0, K, r, SIGMA, T, betas[K])}
    cost_comparison(methods, betas, pd.read_csv(OUT + "e1_convergence.csv")).to_csv(OUT + "e1_variance_reduction.csv", index=False)


if __name__ == "__main__":
    which = sys.argv[1:] or ["e1", "e1seed", "e23", "e4"]
    t0 = time.time()
    if "e1" in which:     experiment1()
    if "e1seed" in which: experiment1(seed=777, tag="_seed777", with_cost=False)    # second seed = noise check
    if "cost" in which:   rerun_cost_only()
    if "e23" in which:    experiment23()
    if "e4" in which:     experiment4()
    print(f"done in {time.time()-t0:.0f}s")
