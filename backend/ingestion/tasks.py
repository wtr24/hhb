from .celery_app import app

@app.task
def health_check_task():
    """Placeholder task to verify Celery worker is processing tasks."""
    return {"status": "celery_ok"}
