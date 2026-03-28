"""
Black-Scholes Greeks calculator.

Provides bs_greeks() for computing option price and Greeks,
and iv_percentile_rank() for computing IV rank.
"""
from scipy.stats import norm
import numpy as np


def bs_greeks(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: str = "call",
) -> dict:
    """
    Compute Black-Scholes option price and Greeks.

    Parameters
    ----------
    S : float
        Current stock price.
    K : float
        Strike price.
    T : float
        Time to expiry in years (e.g. 30/365 for 30 days).
    r : float
        Risk-free rate as decimal (e.g. 0.045 for 4.5%).
    sigma : float
        Implied volatility as decimal (e.g. 0.20 for 20%).
    option_type : str
        'call' or 'put'.

    Returns
    -------
    dict with keys: price, delta, gamma, vega, theta.
    All values are None if T <= 0 or sigma <= 0 (invalid inputs).
    """
    if T <= 0 or sigma <= 0:
        return {"price": None, "delta": None, "gamma": None, "vega": None, "theta": None}

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == "call":
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        delta = norm.cdf(d1)
        theta = (
            -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
            - r * K * np.exp(-r * T) * norm.cdf(d2)
        ) / 365
    else:  # put
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        delta = norm.cdf(d1) - 1
        theta = (
            -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
            + r * K * np.exp(-r * T) * norm.cdf(-d2)
        ) / 365

    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    vega = S * norm.pdf(d1) * np.sqrt(T) / 100  # per 1% IV move

    return {
        "price": round(float(price), 4),
        "delta": round(float(delta), 4),
        "gamma": round(float(gamma), 4),
        "vega": round(float(vega), 4),
        "theta": round(float(theta), 4),
    }


def iv_percentile_rank(current_iv: float, iv_history: list) -> float:
    """
    Compute IV percentile rank: percentage of historical IV values below current_iv.

    Parameters
    ----------
    current_iv : float
        Current implied volatility value.
    iv_history : list[float]
        Historical IV values (at least 1 element required).

    Returns
    -------
    float
        Percentile rank in range 0-100. Returns 0.0 if iv_history is empty.
    """
    if not iv_history:
        return 0.0
    below = sum(1 for v in iv_history if v < current_iv)
    return round(below / len(iv_history) * 100, 2)
