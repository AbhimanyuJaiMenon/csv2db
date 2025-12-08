from app.celery_config import celery_app
from app.tasks import csv_tasks

if __name__ == "__main__":
    celery_app.start()