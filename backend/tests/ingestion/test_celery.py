"""Tests for Celery beat schedule configuration."""
from datetime import timedelta


def test_beat_schedule_has_ohlcv():
    """beat_schedule contains OHLCV entry with correct task name and 5-minute interval."""
    from ingestion.celery_app import app
    schedule = app.conf.beat_schedule
    assert "ingest-ohlcv-every-5min" in schedule
    entry = schedule["ingest-ohlcv-every-5min"]
    assert entry["task"] == "ingestion.tasks.ingest_ohlcv_batch"
    assert entry["schedule"] == timedelta(minutes=5)


def test_beat_schedule_has_macro():
    """beat_schedule contains macro entry with correct task name and 1-hour interval."""
    from ingestion.celery_app import app
    schedule = app.conf.beat_schedule
    assert "ingest-macro-every-1h" in schedule
    entry = schedule["ingest-macro-every-1h"]
    assert entry["task"] == "ingestion.tasks.ingest_macro_batch"
    assert entry["schedule"] == timedelta(hours=1)


def test_beat_schedule_has_fx():
    """beat_schedule contains FX entry with correct task name and 30-second interval."""
    from ingestion.celery_app import app
    schedule = app.conf.beat_schedule
    assert "ingest-fx-every-30s" in schedule
    entry = schedule["ingest-fx-every-30s"]
    assert entry["task"] == "ingestion.tasks.ingest_fx_rates"
    assert entry["schedule"] == timedelta(seconds=30)


def test_beat_schedule_has_treasury():
    """beat_schedule contains treasury entry with correct task name and 15-minute interval."""
    from ingestion.celery_app import app
    schedule = app.conf.beat_schedule
    assert "ingest-treasury-every-15m" in schedule
    entry = schedule["ingest-treasury-every-15m"]
    assert entry["task"] == "ingestion.tasks.ingest_treasury_curve"
    assert entry["schedule"] == timedelta(minutes=15)


def test_beat_schedule_exactly_6_entries():
    """beat_schedule has exactly 4 entries — no extra, no missing."""
    from ingestion.celery_app import app
    assert len(app.conf.beat_schedule) == 6


def test_all_task_names_are_valid():
    """Every task name string in beat_schedule resolves to a real function in ingestion.tasks."""
    import ingestion.tasks as tasks_module
    from ingestion.celery_app import app
    schedule = app.conf.beat_schedule
    for entry_name, entry in schedule.items():
        task_path = entry["task"]
        # task_path format: "ingestion.tasks.<func_name>"
        assert task_path.startswith("ingestion.tasks."), (
            f"{entry_name}: task path '{task_path}' must start with 'ingestion.tasks.'"
        )
        func_name = task_path.split(".")[-1]
        assert hasattr(tasks_module, func_name), (
            f"{entry_name}: function '{func_name}' not found in ingestion.tasks"
        )


def test_celery_app_timezone_utc():
    """Celery app timezone must be UTC."""
    from ingestion.celery_app import app
    assert app.conf.timezone == "UTC"
