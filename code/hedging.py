"""
hedging.py -- Part B: discrete delta hedging of a SHORT European call.

The story, step by step.  The seller sells the call and receives C0 (the exact Black-Scholes price).
At times t_0, t_1, ..., t_{M-1} (t_k = k*dt, dt = T/M) the seller holds delta_k = Phi(d1(t_k, S_{t_k})) shares
and keeps everything else in the bank account.  The portfolio value then evolves as (eq. 8, self-financing):
        V_{k+1} = delta_k * S_{k+1} + ( V_k - delta_k * S_k ) * e^{r dt},        V_0 = C0.
         (new value of the shares)     (cash position, earning interest; negative = borrowed)
At maturity the seller owes (S_T - K)^+.  The discounted hedging error (eq. 9) is
        HE_M = e^{-rT} * ( V_M - (S_T - K)^+ )        (positive = surplus, negative = shortfall).
(eq. 10 shows HE_M also equals a sum of stochastic integrals.)
(The proposal wrote e^{-rT} V_M - (S_T - K)^+, which mixes discounted and undiscounted money; the version above is
the consistent one and is the one that equals the integral formula and has mean zero under Q.)
"""
import numpy as np
from bs_utils import bs_call, bs_delta


def simulate_hedge(S0, K, r, sigma, T, M, n_paths, mus, rng, sigma_hedge=None):
    """
    Simulates n_paths stock paths and delta-hedges the call along each path.

    Inputs
      S0,K,r,sigma,T : model parameters;   M : number of rebalancing dates;   n_paths : number of simulated paths
      mus : LIST of real-world drifts to try (e.g. [0.05, 0.15]).  All drifts are run on the SAME random numbers
            ("common random numbers"), so differences between them are not just simulation noise.
      rng : numpy random generator (fixed seed => reproducible)
      sigma_hedge : volatility used inside delta (default = true sigma; only changes if we study misspecification)

    Each time step:  S_{k+1} = S_k * exp( (mu - sigma^2/2) dt + sigma sqrt(dt) xi ),   xi ~ N(0,1)  (exact GBM step, eq. 1)

    Returns a dictionary {mu: array of the n_paths hedging errors HE_M}.
    """
    if not (S0 > 0 and K > 0 and sigma > 0 and T > 0 and M >= 1 and n_paths >= 2):
        raise ValueError("simulate_hedge: need S0, K, sigma, T > 0, M >= 1 and n_paths >= 2")
    if len(set(mus)) != len(mus):
        raise ValueError("simulate_hedge: duplicate drifts in mus (they are used as dictionary keys)")
    dt = T / M
    sh = sigma if sigma_hedge is None else sigma_hedge
    sq = sigma * np.sqrt(dt)                           # volatility of one step
    drift = {mu: (mu - 0.5 * sigma**2) * dt for mu in mus}   # log-drift of one step, per real-world drift
    C0 = bs_call(S0, K, r, sh, T)                     # premium received at time 0
    growth = np.exp(r * dt)                           # one step of bank-account growth
    S = {mu: np.full(n_paths, float(S0)) for mu in mus}   # current stock price on every path, one array per drift
    V = {mu: np.full(n_paths, float(C0)) for mu in mus}   # current portfolio value on every path
    for k in range(M):
        xi = rng.standard_normal(n_paths)             # the random shock of this step (shared by all drifts)
        tau = T - k * dt                              # time left to maturity at t_k
        for mu in mus:
            delta = bs_delta(S[mu], K, r, sh, tau)    # shares to hold during this step
            S_next = S[mu] * np.exp(drift[mu] + sq * xi)
            V[mu] = delta * S_next + (V[mu] - delta * S[mu]) * growth     # eq. 8
            S[mu] = S_next
    # S now holds S_T and V holds V_M
    return {mu: np.exp(-r * T) * (V[mu] - np.maximum(S[mu] - K, 0.0)) for mu in mus}   # eq. 9
