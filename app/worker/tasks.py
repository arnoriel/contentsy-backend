from app.worker.celery_app import celery_app


@celery_app.task(name="contentsy.ping")
def ping() -> str:
    """Dummy task buat verifikasi worker terima task (BE-Azriel-01)."""
    return "pong"
