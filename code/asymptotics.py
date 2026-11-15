"""
asymptotics.py -- Experiment 4: the theoretical prediction for the size of the hedging error.

Idea (full explanation in the learning guide).  Each rebalancing step makes an error whose variance is about
    (1/2) sigma^4 e^{-2 r t_k} (S^2 Gamma)^2 dt^2     (eq. 11, from the Gamma expansion),
so adding up M independent steps gives (eq. 12)
    Var(HE_M)  ~  a * dt,     a = (sigma^4 / 2) * Integral_0^T  e^{-2rt} E[ (S_t^2 Gamma(t,S_t))^2 ] dt.
The quantity S^2*Gamma ("dollar gamma") is the sensitivity of the hedge to the stock price.

The expectation E[(S^2 Gamma)^2] can be done exactly: ln S_t is normal and d1 is a linear function of the normal
variable, so the integrand is exp(quadratic) and the integral is a standard Gaussian integral (see guide).
"""
import numpy as np
from scipy.integrate import quad


def second_moment_S2Gamma(t, S0, K, r, sigma, T, mu=None):
    """
    Returns E[ (S_t^2 * Gamma(t, S_t))^2 ] at calendar time t (0 <= t < T).
    mu is the drift of the stock used when taking the expectation: mu = r (default) = risk-neutral world,
    any other value = real-world expectation.
    Method: write ln S_t = m + s*z with z ~ N(0,1);  then d1 = a*z + c is linear in z and
    S^2 Gamma = S phi(d1) / (sigma sqrt(tau)), so the integrand is exp(alpha + beta z - q z^2): a Gaussian integral.
    """
    mu = r if mu is None else mu
    tau = T - t
    m = np.log(S0) + (mu - 0.5 * sigma**2) * t                 # mean of ln S_t
    s = sigma * np.sqrt(t)                                     # standard deviation of ln S_t
    a = s / (sigma * np.sqrt(tau))                             # d1 = a z + c
    c = (m - np.log(K) + (r + 0.5 * sigma**2) * tau) / (sigma * np.sqrt(tau))
    q = a * a + 0.5                                            # coefficient of -z^2 in the exponent
    lin = 2 * s - 2 * a * c                                    # coefficient of z in the exponent
    expo = 2 * m - c * c + lin * lin / (4 * q)                 # value of the exponent after completing the square
    integral = np.exp(expo) * np.sqrt(np.pi / q)
    return integral / (2 * np.pi * np.sqrt(2 * np.pi)) / (sigma**2 * tau)


def asymptotic_constant(S0, K, r, sigma, T, mu=None):
    """
    Returns a in  Var(HE_M) ~ a * dt   (eq. 12), computed by numerical integration over t.
    Near t = T the integrand behaves like 1/sqrt(T-t) (large but integrable); the substitution T - t = u^2
    turns this into a smooth integrand, which is why the code integrates over u instead of t.
    """
    f = lambda u: 2 * u * np.exp(-2 * r * (T - u * u)) * second_moment_S2Gamma(T - u * u, S0, K, r, sigma, T, mu)
    val, _ = quad(f, 0.0, np.sqrt(T), limit=200)
    return 0.5 * sigma**4 * val


def discrete_sum_variance(M, S0, K, r, sigma, T, mu=None):
    """
    Same prediction but with the integral replaced by the actual sum over the M rebalancing dates t_k = k dt:
        Var(HE_M) ~ (sigma^4 dt^2 / 2) * sum_{k=0}^{M-1} e^{-2 r t_k} E[(S^2 Gamma)^2](t_k).
    This is more accurate for small M because it does not pretend the dates are infinitely close together.
    """
    dt = T / M
    tk = np.arange(M) * dt
    vals = np.exp(-2 * r * tk) * second_moment_S2Gamma(tk, S0, K, r, sigma, T, mu)   # works on the whole array at once
    return 0.5 * sigma**4 * dt**2 * vals.sum()


# ---------------------------------------------------------------------------------------------------------
# Hedging with a WRONG volatility (experiment E5).  The seller prices and hedges with sigma_hat while the stock
# really has volatility sigma.  Ito on the discounted BS value C(t,S;sigma_hat) gives, for continuous trading,
#     HE = (1/2) (sigma_hat^2 - sigma^2) * Integral_0^T e^{-rt} (S_t^2 Gamma_hat(t,S_t)) dt ,
# so the MEAN error does not vanish as M grows.  Its expectation (stock with true sigma, drift mu) is below.
# ---------------------------------------------------------------------------------------------------------
def first_moment_S2Gamma_hat(t, S0, K, r, sigma, sigma_hat, T, mu=None):
    """E[ S_t^2 * Gamma_hat(t, S_t) ] where S_t has true volatility sigma and Gamma_hat uses sigma_hat (Gaussian integral)."""
    mu = r if mu is None else mu
    tau = T - t
    m = np.log(S0) + (mu - 0.5 * sigma**2) * t
    s = sigma * np.sqrt(t)
    a = s / (sigma_hat * np.sqrt(tau))
    c = (m - np.log(K) + (r + 0.5 * sigma_hat**2) * tau) / (sigma_hat * np.sqrt(tau))
    q = 0.5 * (a * a + 1.0)
    lin = s - a * c
    integral = np.exp(m - 0.5 * c * c + lin * lin / (4 * q)) * np.sqrt(np.pi / q) / (2 * np.pi)
    return integral / (sigma_hat * np.sqrt(tau))


def mean_wrong_vol(S0, K, r, sigma, sigma_hat, T):
    """Theoretical mean of the (discounted) hedging error when hedging with sigma_hat (continuous-trading limit)."""
    f = lambda u: 2 * u * np.exp(-r * (T - u * u)) * first_moment_S2Gamma_hat(T - u * u, S0, K, r, sigma, sigma_hat, T)
    val, _ = quad(f, 0.0, np.sqrt(T), limit=200)
    return 0.5 * (sigma_hat**2 - sigma**2) * val
