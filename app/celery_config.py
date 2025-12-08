from celery import Celery

celery_app = Celery(
    "csv_processor",
    broker="pyamqp://guest@localhost//",
    backend="rpc://",
    include=["app.tasks.csv_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
)

