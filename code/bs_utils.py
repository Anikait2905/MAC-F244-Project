"""
bs_utils.py -- Black-Scholes closed-form formulas.  These are the "exact answers" we compare everything against.

Notation used in every function:
    S      current stock price           K     strike price
    r      risk-free interest rate       sigma volatility
    tau    time to maturity = T - t  (must be > 0)
"""
import numpy as np
from scipy.special import ndtr          # ndtr(x) = Phi(x), the standard normal cdf (fast, works on arrays)


def phi(x):
    """Standard normal density  phi(x) = exp(-x^2/2) / sqrt(2*pi)."""
    return np.exp(-0.5 * x * x) / np.sqrt(2.0 * np.pi)


def d1_d2(S, K, r, sigma, tau):
    """
    Returns (d1, d2) of the Black-Scholes formula.
        d1 = [ln(S/K) + (r + sigma^2/2) tau] / (sigma sqrt(tau)),    d2 = d1 - sigma sqrt(tau)
    d1 and d2 are "how many standard deviations in the money" the option is (in two slightly different senses).
    """
    sd = sigma * np.sqrt(tau)
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * tau) / sd
    return d1, d1 - sd


def bs_call(S, K, r, sigma, tau):
    """Black-Scholes call price (eq. 3):  C = S Phi(d1) - K e^{-r tau} Phi(d2)."""
    d1, d2 = d1_d2(S, K, r, sigma, tau)
    return S * ndtr(d1) - K * np.exp(-r * tau) * ndtr(d2)


def bs_put(S, K, r, sigma, tau):
    """Black-Scholes put price: P = K e^{-r tau} Phi(-d2) - S Phi(-d1).  Used only for the put-call parity check."""
    d1, d2 = d1_d2(S, K, r, sigma, tau)
    return K * np.exp(-r * tau) * ndtr(-d2) - S * ndtr(-d1)


def bs_delta(S, K, r, sigma, tau):
    """Delta = dC/dS = Phi(d1)  (eq. 4): the number of shares that moves like the option."""
    d1, _ = d1_d2(S, K, r, sigma, tau)
    return ndtr(d1)


def bs_gamma(S, K, r, sigma, tau):
    """Gamma = d^2C/dS^2 = phi(d1) / (S sigma sqrt(tau))  (eq. 4): how fast delta changes when S changes."""
    d1, _ = d1_d2(S, K, r, sigma, tau)
    return phi(d1) / (S * sigma * np.sqrt(tau))
