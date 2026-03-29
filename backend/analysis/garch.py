"""
GARCH(1,1) volatility computation using the arch library.

Isolated from indicators.py because arch imports are heavyweight.
Called from the /api/ta/indicators route for TA-04 volatility.
"""
import numpy as np


def compute_garch_volatility(closes: np.ndarray) -> dict:
    """
    Fit GARCH(1,1) to log returns and return fitted parameters + 1-day forecast.

    Returns {"omega", "alpha", "beta", "vol_1d_forward"} on success.
    Returns {"error": "..."} if fitting fails or insufficient data (<100 bars).

    Minimum 100 bars required — raises no exception, returns error dict instead.
    Wrap arch_model in try/except to handle ConvergenceWarning (Pitfall 7).
    """
    from arch import arch_model
    if len(closes) < 100:
        return {"error": "insufficient data — need at least 100 bars for GARCH"}
    returns = np.diff(np.log(closes)) * 100  # percentage log returns
    try:
        am = arch_model(returns, vol="Garch", p=1, q=1, dist="Normal")
        res = am.fit(disp="off")  # suppress convergence output to stdout
        forecast = res.forecast(horizon=1)
        vol_1d = float(np.sqrt(forecast.variance.values[-1, 0])) / 100
        # Sanity check: NaN params indicate failed fit
        if np.isnan(res.params["omega"]) or np.isnan(res.params["alpha[1]"]):
            return {"error": "garch fitting produced NaN parameters"}
        return {
            "omega": round(float(res.params["omega"]), 6),
            "alpha": round(float(res.params["alpha[1]"]), 6),
            "beta": round(float(res.params["beta[1]"]), 6),
            "vol_1d_forward": round(vol_1d, 6),
        }
    except Exception as e:
        return {"error": f"garch fitting failed: {str(e)[:100]}"}
