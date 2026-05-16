"""Celery app: queues for slow / retryable background work.

Routing:
  • ingest   — re-ingest tasks (manual refresh, full vault rescan)
  • classify — re-classify (model upgrade, prompt rollover)
  • report   — build daily/weekly reports off the cron path
  • pdf      — synchronous PDF render fallback
  • sync     — archive moves + WS replay
"""

import os

from celery import Celery

broker = os.environ.get("CELERY_BROKER_URL") or os.environ["REDIS_URL"]
backend = os.environ.get("CELERY_RESULT_BACKEND") or broker

app = Celery("intelligence-workers", broker=broker, backend=backend)
app.conf.update(
    task_acks_late=True,
    task_default_retry_delay=2,
    task_max_retries=5,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    worker_prefetch_multiplier=1,
)
app.conf.task_routes = {
    "workers.ingest.*": {"queue": "ingest"},
    "workers.classify.*": {"queue": "classify"},
    "workers.report.*": {"queue": "report"},
    "workers.pdf.*": {"queue": "pdf"},
    "workers.sync.*": {"queue": "sync"},
}

# auto-import tasks
import workers.tasks_ingest  # noqa: F401, E402
import workers.tasks_sync    # noqa: F401, E402
