"""
Schema tests for Phase 2 ingestion hypertable models.

These tests verify that the SQLAlchemy model definitions have the correct
table names, primary key columns, and column counts — without requiring a
live database connection.
"""
import pytest
from sqlalchemy import inspect as sa_inspect

from models.fundamentals import Fundamentals
from models.macro_series import MacroSeries
from models.fx_rate import FXRate
from models.yield_curve import YieldCurve
from models.ohlcv import OHLCV


def _pk_columns(model):
    """Return the list of primary key column names for a model."""
    mapper = sa_inspect(model)
    return [col.key for col in mapper.mapper.column_attrs if col.columns[0].primary_key]


def _all_columns(model):
    """Return all column names for a model."""
    mapper = sa_inspect(model)
    return [col.key for col in mapper.mapper.column_attrs]


# ------------------------------------------------------------------ #
# Table name tests
# ------------------------------------------------------------------ #

def test_fundamentals_table_name():
    assert Fundamentals.__tablename__ == "fundamentals"


def test_macro_series_table_name():
    assert MacroSeries.__tablename__ == "macro_series"


def test_fx_rates_table_name():
    assert FXRate.__tablename__ == "fx_rates"


def test_yield_curve_table_name():
    assert YieldCurve.__tablename__ == "yield_curve"


# ------------------------------------------------------------------ #
# Primary key tests
# ------------------------------------------------------------------ #

def test_fundamentals_pk_is_time_and_ticker():
    pks = _pk_columns(Fundamentals)
    assert "time" in pks
    assert "ticker" in pks


def test_macro_series_pk_is_time_and_series_id():
    pks = _pk_columns(MacroSeries)
    assert "time" in pks
    assert "series_id" in pks


def test_fx_rates_pk_is_time_base_quote():
    pks = _pk_columns(FXRate)
    assert "time" in pks
    assert "base" in pks
    assert "quote" in pks


def test_yield_curve_pk_is_time_only():
    pks = _pk_columns(YieldCurve)
    assert pks == ["time"]


# ------------------------------------------------------------------ #
# Column count / presence tests
# ------------------------------------------------------------------ #

def test_fundamentals_has_expected_columns():
    cols = _all_columns(Fundamentals)
    for expected in ["time", "ticker", "pe_ratio", "ev_ebitda", "market_cap", "debt_equity", "source"]:
        assert expected in cols, f"Missing column: {expected}"


def test_macro_series_has_expected_columns():
    cols = _all_columns(MacroSeries)
    for expected in ["time", "series_id", "value", "source"]:
        assert expected in cols, f"Missing column: {expected}"


def test_fx_rates_has_expected_columns():
    cols = _all_columns(FXRate)
    for expected in ["time", "base", "quote", "rate", "source"]:
        assert expected in cols, f"Missing column: {expected}"


def test_yield_curve_has_12_tenor_columns():
    cols = _all_columns(YieldCurve)
    tenors = [
        "bc_1month", "bc_2month", "bc_3month", "bc_6month",
        "bc_1year", "bc_2year", "bc_3year", "bc_5year",
        "bc_7year", "bc_10year", "bc_20year", "bc_30year",
    ]
    assert len(tenors) == 12, "Tenor list should contain exactly 12 entries"
    for tenor in tenors:
        assert tenor in cols, f"Missing tenor column: {tenor}"


def test_ohlcv_table_name_unchanged():
    """Regression: migration 0002 must not affect the existing ohlcv table name."""
    assert OHLCV.__tablename__ == "ohlcv"
