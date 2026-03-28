"""
Insider transaction clustering logic.

Filters 10b5-1/award/disposition codes and clusters open-market
purchases and sales by proximity in time.
"""
from datetime import datetime, timedelta


# Transaction codes to EXCLUDE (10b5-1 tax payments, awards, dispositions)
_EXCLUDE_CODES = {"F", "A", "D"}
# Transaction codes to INCLUDE (open-market purchases and sales)
_INCLUDE_CODES = {"P", "S"}


def cluster_insiders(transactions: list, window_days: int = 14) -> dict:
    """
    Filter and cluster insider transactions.

    Parameters
    ----------
    transactions : list[dict]
        Finnhub insider transaction dicts. Required keys per transaction:
          name, share, change, filingDate, transactionDate,
          transactionCode, transactionPrice, isDerivative
    window_days : int
        Maximum days between transactions to consider them a cluster (default 14).

    Returns
    -------
    dict with keys:
      buy_count    : int   — number of open-market purchase transactions
      sell_count   : int   — number of open-market sale transactions
      buy_sell_ratio : float|None — buy_count / sell_count, None if sell_count == 0
      clusters     : list[dict]  — time-proximity clusters
        each cluster: {start_date, end_date, transactions: [...]}
      multi_insider : bool — True if 2+ distinct names bought in same cluster window
    """
    # Filter to open-market buys and sells only
    filtered = [
        t for t in transactions
        if t.get("transactionCode") in _INCLUDE_CODES
    ]

    buy_count = sum(1 for t in filtered if t.get("transactionCode") == "P")
    sell_count = sum(1 for t in filtered if t.get("transactionCode") == "S")

    buy_sell_ratio = None
    if sell_count > 0:
        buy_sell_ratio = round(buy_count / sell_count, 4)

    # Build clusters by transaction date proximity
    clusters = _build_clusters(filtered, window_days)

    # multi_insider: any cluster where 2+ distinct names made purchases
    multi_insider = False
    for cluster in clusters:
        buyers = {t["name"] for t in cluster["transactions"] if t.get("transactionCode") == "P"}
        if len(buyers) >= 2:
            multi_insider = True
            break

    return {
        "buy_count": buy_count,
        "sell_count": sell_count,
        "buy_sell_ratio": buy_sell_ratio,
        "clusters": clusters,
        "multi_insider": multi_insider,
    }


def _build_clusters(transactions: list, window_days: int) -> list:
    """
    Group transactions into time-proximity clusters.

    A cluster starts with the earliest transaction and extends to any
    transaction within window_days of the cluster's start_date.
    """
    if not transactions:
        return []

    # Parse and sort by transactionDate
    def _parse_date(t: dict):
        raw = t.get("transactionDate") or t.get("filingDate") or ""
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    dated = []
    for t in transactions:
        d = _parse_date(t)
        if d is not None:
            dated.append((d, t))

    if not dated:
        return []

    dated.sort(key=lambda x: x[0])

    clusters = []
    used = [False] * len(dated)

    for i, (date_i, txn_i) in enumerate(dated):
        if used[i]:
            continue
        cluster_txns = [txn_i]
        used[i] = True
        cluster_start = date_i
        cluster_end = date_i

        for j, (date_j, txn_j) in enumerate(dated):
            if used[j]:
                continue
            if (date_j - cluster_start).days <= window_days:
                cluster_txns.append(txn_j)
                used[j] = True
                if date_j > cluster_end:
                    cluster_end = date_j

        clusters.append({
            "start_date": str(cluster_start),
            "end_date": str(cluster_end),
            "transactions": cluster_txns,
        })

    return clusters
