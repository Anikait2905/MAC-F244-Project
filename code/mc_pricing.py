"""
mc_pricing.py -- Part A: Monte Carlo pricing of a European call.

Goal: estimate C0 = e^{-rT} E_Q[(S_T - K)^+]   (price = discounted expected payoff in the risk-neutral world Q).

Three estimators.  Each takes standard normal random numbers Z and returns (estimate, standard_error).
Fair-comparison rule used everywhere: every estimator uses the same number N of payoff evaluations.
"""
import numpy as np


def terminal_price(Z, S0, r, sigma, T):
    """
    Turns standard normals into possible stock prices at time T, using the exact GBM solution under Q (eq. 2):
        S_T = S0 * exp( (r - sigma^2/2) T + sigma sqrt(T) Z ).
    Input : array Z of N(0,1) numbers.       Returns: array of simulated terminal prices.
    """
    return S0 * np.exp((r - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * Z)


def discounted_call_payoff(ST, K, r, T):
    """Y = e^{-rT} * max(S_T - K, 0): what the option pays at T, expressed in today's money."""
    return np.exp(-r * T) * np.maximum(ST - K, 0.0)


# ------------------------------------------------------------------ estimator 1: plain Monte Carlo
def mc_plain(Z, S0, K, r, sigma, T):
    """
    Plain Monte Carlo (eq. 5).  Input: N normals.  Returns (C_hat, SE) with
        C_hat = average of the N discounted payoffs,     SE = (sample sd of the payoffs) / sqrt(N).
    """
    Y = discounted_call_payoff(terminal_price(Z, S0, r, sigma, T), K, r, T)
    return Y.mean(), Y.std(ddof=1) / np.sqrt(len(Y))


# ------------------------------------------------------------------ estimator 2: antithetic variates
def mc_antithetic(Zhalf, S0, K, r, sigma, T):
    """
    Antithetic variates (eq. 6).  Input: only N/2 normals (each one is used twice: as Z and as -Z),
    so the total number of payoff evaluations is N, the same as plain MC.
        pair average  W_i = ( Y(Z_i) + Y(-Z_i) ) / 2,      C_hat = average of the W_i.
    IMPORTANT: the SE uses the N/2 pair averages W_i (they are independent of each other);
    the two payoffs inside one pair are NOT independent, so we must not treat all N payoffs as independent.
    """
    if len(Zhalf) < 2:
        raise ValueError("mc_antithetic: need at least 2 antithetic pairs")
    Yplus  = discounted_call_payoff(terminal_price( Zhalf, S0, r, sigma, T), K, r, T)
    Yminus = discounted_call_payoff(terminal_price(-Zhalf, S0, r, sigma, T), K, r, T)
    W = 0.5 * (Yplus + Yminus)
    return W.mean(), W.std(ddof=1) / np.sqrt(len(W))


# ------------------------------------------------------------------ estimator 3: control variate
def estimate_beta(S0, K, r, sigma, T, n_pilot=100_000, seed=12345):
    """
    Finds the control-variate coefficient  beta = Cov(Y, X) / Var(X),  with X = e^{-rT} S_T.
    It is computed from a SEPARATE pilot sample so that beta is just a fixed number when we use it later
    (this keeps the final estimator exactly unbiased).
    """
    Z = np.random.default_rng(seed).standard_normal(n_pilot)
    ST = terminal_price(Z, S0, r, sigma, T)
    Y = discounted_call_payoff(ST, K, r, T)
    X = np.exp(-r * T) * ST
    return np.cov(Y, X)[0, 1] / X.var(ddof=1)


def mc_control_variate(Z, S0, K, r, sigma, T, beta):
    """
    Control variate (eq. 7).  The discounted stock X = e^{-rT} S_T has a KNOWN expected value: E_Q[X] = S0.
        corrected payoff  A_i = Y_i - beta (X_i - S0),     C_hat = average of A_i,   SE = sd(A_i)/sqrt(N).
    Because E[X - S0] = 0, subtracting beta(X - S0) does not change the expected value, only the spread.
    """
    ST = terminal_price(Z, S0, r, sigma, T)
    Y = discounted_call_payoff(ST, K, r, T)
    X = np.exp(-r * T) * ST
    A = Y - beta * (X - S0)
    return A.mean(), A.std(ddof=1) / np.sqrt(len(A))
