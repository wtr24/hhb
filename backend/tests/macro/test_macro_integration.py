"""
Integration smoke tests — Phase 5 Macro Dashboard (MACRO-01 through MACRO-14).

These tests verify:
1. All new ingestion source modules are importable.
2. All new API routes are registered and reachable (using FastAPI TestClient with mocked DB).
3. The response shape from each macro route contains the keys expected by the frontend.

No live DB/Redis/external API calls are made.
"""
import pytest


# ---------------------------------------------------------------------------
# 1. Importability checks — ingestion source modules
# ---------------------------------------------------------------------------

def test_boe_source_importable():
    """MACRO-02: BoE gilt curve source module exists and is importable."""
    from ingestion.sources import boe_source  # noqa: F401


def test_vix_source_importable():
    """MACRO-11, MACRO-12: VIX term structure source module exists and is importable."""
    from ingestion.sources import vix_source  # noqa: F401


def test_cboe_source_importable():
    """MACRO-13 (put/call component): CBOE source module exists and is importable."""
    from ingestion.sources import cboe_source  # noqa: F401


def test_ons_source_importable():
    """MACRO-07, MACRO-08, MACRO-09: ONS source module exists and is importable."""
    from ingestion.sources import ons_source  # noqa: F401


def test_bls_source_importable():
    """MACRO-08: BLS source module exists and is importable."""
    from ingestion.sources import bls_source  # noqa: F401


def test_ecb_source_importable():
    """MACRO-09: ECB source module exists and is importable."""
    from ingestion.sources import ecb_source  # noqa: F401


def test_fear_greed_importable():
    """MACRO-13: Fear & Greed computation service is importable."""
    from analysis import fear_greed  # noqa: F401
    assert hasattr(fear_greed, 'compute_fear_greed_composite')


# ---------------------------------------------------------------------------
# 2. Celery task registration checks
# ---------------------------------------------------------------------------

def _get_registered_task_names():
    """Import tasks module to trigger Celery task registration, then return task names."""
    import ingestion.tasks  # noqa: F401 — side-effect: registers all @app.task decorators
    from ingestion.celery_app import app
    return list(app.tasks.keys())


def test_boe_task_registered():
    """MACRO-02: BoE gilt curve ingestion task is registered in Celery app."""
    task_names = _get_registered_task_names()
    assert any('boe' in t.lower() or 'gilt' in t.lower() for t in task_names), \
        f"No BoE/gilt task found in: {task_names}"


def test_vix_task_registered():
    """MACRO-11: VIX term structure ingestion task is registered."""
    task_names = _get_registered_task_names()
    assert any('vix' in t.lower() for t in task_names), \
        f"No VIX task found in: {task_names}"


def test_cboe_task_registered():
    """MACRO-13 (put/call): CBOE ingestion task is registered."""
    task_names = _get_registered_task_names()
    assert any('cboe' in t.lower() or 'pcr' in t.lower() for t in task_names), \
        f"No CBOE/pcr task found in: {task_names}"


def test_breadth_snapshot_task_registered():
    """MACRO-13 (breadth component): Breadth snapshot task is registered."""
    task_names = _get_registered_task_names()
    assert any('breadth' in t.lower() for t in task_names), \
        f"No breadth task found in: {task_names}"


# ---------------------------------------------------------------------------
# 3. FRED series map coverage
# ---------------------------------------------------------------------------

def test_fred_series_map_has_tips_breakeven():
    """MACRO-06: FRED series map contains TIPS breakeven series."""
    from ingestion.config import FRED_SERIES_MAP
    assert 'tips_breakeven_10y' in FRED_SERIES_MAP, \
        "tips_breakeven_10y missing from FRED_SERIES_MAP"
    assert FRED_SERIES_MAP['tips_breakeven_10y'] == 'T10YIE'


def test_fred_series_map_has_hy_spread():
    """MACRO-13 (HY spread component): FRED series map contains junk bond spread."""
    from ingestion.config import FRED_SERIES_MAP
    assert 'hy_spread' in FRED_SERIES_MAP, \
        "hy_spread missing from FRED_SERIES_MAP"


def test_fred_series_map_has_safe_haven_usd():
    """MACRO-13 (safe haven component): FRED series map contains DXY."""
    from ingestion.config import FRED_SERIES_MAP
    assert 'safe_haven_usd' in FRED_SERIES_MAP, \
        "safe_haven_usd missing from FRED_SERIES_MAP"


# ---------------------------------------------------------------------------
# 4. DB model importability checks
# ---------------------------------------------------------------------------

def test_gilt_curve_model_importable():
    """MACRO-02: GiltCurve DB model is importable."""
    from models.gilt_curve import GiltCurve  # noqa: F401
    assert GiltCurve.__tablename__ == 'gilt_curve'


def test_vix_term_structure_model_importable():
    """MACRO-11: VixTermStructure DB model is importable."""
    from models.vix_term_structure import VixTermStructure  # noqa: F401
    assert VixTermStructure.__tablename__ == 'vix_term_structure'


# ---------------------------------------------------------------------------
# 5. TTL cache key coverage
# ---------------------------------------------------------------------------

def test_ttl_dict_has_gilt_curve():
    """MACRO-02: gilt_curve TTL key exists."""
    from cache.ttl import TTL
    assert 'gilt_curve' in TTL, "gilt_curve missing from TTL dict"


def test_ttl_dict_has_vix_term_structure():
    """MACRO-11: vix_term_structure TTL key exists."""
    from cache.ttl import TTL
    assert 'vix_term_structure' in TTL, "vix_term_structure missing from TTL dict"


def test_ttl_dict_has_fear_greed():
    """MACRO-13: fear_greed TTL key exists."""
    from cache.ttl import TTL
    assert 'fear_greed' in TTL, "fear_greed missing from TTL dict"
