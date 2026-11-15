"""
validate.py -- basic correctness checks (run before the experiments).  Prints PASS/FAIL lines.
"""
import sys
import numpy as np
from scipy.integrate import quad
from bs_utils import bs_call, bs_put, bs_delta, bs_gamma, d1_d2, phi
from mc_pricing import terminal_price, mc_plain, mc_antithetic, mc_control_variate, estimate_beta
from hedging import simulate_hedge
from asymptotics import second_moment_S2Gamma, asymptotic_constant, discrete_sum_variance

from config import S0, R as r, SIGMA as sigma, T
ok_all = True
def check(name, cond, info=""):
    global ok_all
    ok_all &= bool(cond)
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {info}")

# (i) Black-Scholes against a textbook value (S=K=100, r=5%, sigma=20%, T=1  ->  10.4506)
check("BS call value 10.4506", abs(bs_call(S0, 100, r, sigma, T) - 10.4506) < 1e-4, f"{bs_call(S0,100,r,sigma,T):.4f}")

# (ii) put-call parity (analytic):  C - P = S0 - K e^{-rT}
for K in (90, 100, 110):
    lhs = bs_call(S0, K, r, sigma, T) - bs_put(S0, K, r, sigma, T)
    check(f"put-call parity K={K}", abs(lhs - (S0 - K*np.exp(-r*T))) < 1e-10)

# (iii) finite-difference check of Delta and Gamma
h = 1e-3
for K in (90, 100, 110):
    fd_delta = (bs_call(S0+h, K, r, sigma, T) - bs_call(S0-h, K, r, sigma, T)) / (2*h)
    fd_gamma = (bs_call(S0+h, K, r, sigma, T) - 2*bs_call(S0, K, r, sigma, T) + bs_call(S0-h, K, r, sigma, T)) / h**2
    check(f"FD delta K={K}", abs(fd_delta - bs_delta(S0, K, r, sigma, T)) < 1e-6)
    check(f"FD gamma K={K}", abs(fd_gamma - bs_gamma(S0, K, r, sigma, T)) < 1e-5)

# (iv) martingale test  E[e^{-rT} S_T] = S0  (equivalent to MC put-call parity)
Z = np.random.default_rng(0).standard_normal(1_000_000)
X = np.exp(-r*T) * terminal_price(Z, S0, r, sigma, T)
se = X.std(ddof=1)/np.sqrt(len(X))
check("martingale E[e^{-rT}S_T]=S0", abs(X.mean()-S0) < 3*se, f"mean={X.mean():.4f}, 3se={3*se:.4f}")

# (v) each MC estimator lands within 3 SE of Black-Scholes; same seed -> same answer
for K in (90, 100, 110):
    exact = bs_call(S0, K, r, sigma, T)
    beta = estimate_beta(S0, K, r, sigma, T)
    for name, f in [("plain", lambda z: mc_plain(z, S0, K, r, sigma, T)),
                    ("antithetic", lambda z: mc_antithetic(z[: len(z)//2], S0, K, r, sigma, T)),
                    ("control", lambda z: mc_control_variate(z, S0, K, r, sigma, T, beta))]:
        est, se = f(Z)
        check(f"MC {name} K={K}", abs(est-exact) < 3*se, f"est={est:.4f} exact={exact:.4f} se={se:.4f}")
Z2 = np.random.default_rng(0).standard_normal(1_000_000)
check("reproducible seed", mc_plain(Z, S0, 100, r, sigma, T) == mc_plain(Z2, S0, 100, r, sigma, T))

# (vi) hedging: mean HE under Q is ~0 ;  HE -> 0 as M grows
rng = np.random.default_rng(1)
he = simulate_hedge(S0, 100, r, sigma, T, 52, 200_000, [r], rng)[r]
z = he.mean()/(he.std(ddof=1)/np.sqrt(len(he)))
check("mean HE under Q ~ 0 (M=52)", abs(z) < 3.5, f"z={z:.2f}")
sds = [simulate_hedge(S0, 100, r, sigma, T, M, 20_000, [r], np.random.default_rng(2))[r].std() for M in (10, 40, 160)]
check("sd(HE) decreasing in M", sds[0] > sds[1] > sds[2], f"{np.round(sds,3)}")

# (vii) closed form E[(S^2 Gamma)^2] against direct numerical quadrature over z
K, t = 100.0, 0.4
def integrand(z):
    St = S0*np.exp((r-0.5*sigma**2)*t + sigma*np.sqrt(t)*z)
    return (St**2*bs_gamma(St, K, r, sigma, T-t))**2 * phi(z)
num, _ = quad(integrand, -10, 10, limit=400)
check("closed-form 2nd moment == quadrature", abs(num/second_moment_S2Gamma(t, S0, K, r, sigma, T) - 1) < 1e-6,
      f"{num:.6f} vs {second_moment_S2Gamma(t,S0,K,r,sigma,T):.6f}")

# (viii) guards and the antithetic estimator's calibration
try:
    simulate_hedge(S0, 100, r, sigma, T, 0, 10, [r], np.random.default_rng(0)); guard_ok = False
except ValueError:
    guard_ok = True
check("simulate_hedge rejects M = 0", guard_ok)
try:
    mc_antithetic(np.array([0.1]), S0, 100, r, sigma, T); guard_ok = False
except ValueError:
    guard_ok = True
check("mc_antithetic rejects a single pair", guard_ok)
K = 100; exact = bs_call(S0, K, r, sigma, T)
res = np.array([mc_antithetic(np.random.default_rng(i).standard_normal(5000), S0, K, r, sigma, T) for i in range(300)])
check("antithetic unbiased", abs(res[:, 0].mean() - exact) < 3 * res[:, 0].std() / np.sqrt(300), f"mean err={res[:,0].mean()-exact:.4f}")
check("antithetic SE calibrated", 0.8 < res[:, 0].std() / res[:, 1].mean() < 1.2, f"sd/mean SE={res[:,0].std()/res[:,1].mean():.3f}")
beta = estimate_beta(S0, K, r, sigma, T)
resc = np.array([mc_control_variate(np.random.default_rng(1000 + i).standard_normal(5000), S0, K, r, sigma, T, beta) for i in range(300)])
check("control variate unbiased", abs(resc[:, 0].mean() - exact) < 3 * resc[:, 0].std() / np.sqrt(300), f"mean err={resc[:,0].mean()-exact:.4f}")
check("control variate SE calibrated", 0.8 < resc[:, 0].std() / resc[:, 1].mean() < 1.2, f"sd/mean SE={resc[:,0].std()/resc[:,1].mean():.3f}")

# (ix) E5/E6 extensions: wrong-volatility theory (mean error = premium mis-pricing) and the real-data file
from asymptotics import mean_wrong_vol
sh = 0.3
th = mean_wrong_vol(S0, 100, r, sigma, sh, T)
check("wrong-vol theory == BS price gap", abs(th - (bs_call(S0, 100, r, sh, T) - bs_call(S0, 100, r, sigma, T))) < 1e-6, f"{th:.4f}")
he_w = simulate_hedge(S0, 100, r, sigma, T, 252, 50_000, [r], np.random.default_rng(5), sigma_hedge=sh)[r]
check("wrong-vol simulation matches theory (1%)", abs(he_w.mean() / th - 1) < 0.01, f"sim={he_w.mean():.3f} theory={th:.3f}")
import pandas as pd
from config import ROOT
_sp = pd.to_numeric(pd.read_csv(ROOT / "data" / "sp500_fred.csv")["SP500"], errors="coerce").dropna()
check("S&P 500 data file has > 2000 daily closes", len(_sp) > 2000, f"{len(_sp)} rows")

print("\nALL CHECKS PASSED" if ok_all else "\nSOME CHECKS FAILED")
sys.exit(0 if ok_all else 1)   # non-zero exit status lets run_all.sh (set -e) stop on a failed check
