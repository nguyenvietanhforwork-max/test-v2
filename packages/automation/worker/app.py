"""Celery app — workers consume the Redis Stream and drive the LangGraph pipeline.

Run:
    celery -A packages.automation.worker.app worker --loglevel=info --concurrency=4
    celery -A packages.automation.worker.app beat   --loglevel=info
"""

from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

celery = Celery(
    "atlas",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "packages.automation.worker.tasks",
    ],
)

celery.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_max_tasks_per_child=200,
    worker_prefetch_multiplier=1,        # fair scheduling for long LLM calls
    task_default_queue="atlas.default",
    task_routes={
        "atlas.ingest.process_file": {"queue": "atlas.ingest"},
        "atlas.reports.build_daily": {"queue": "atlas.reports"},
        "atlas.reports.build_weekly": {"queue": "atlas.reports"},
        "atlas.maintenance.reconcile": {"queue": "atlas.maintenance"},
    },
    timezone="Asia/Ho_Chi_Minh",
)

# Scheduled jobs
celery.conf.beat_schedule = {
    "daily-brief-0600": {
        "task": "atlas.reports.build_daily",
        "schedule": crontab(hour=6, minute=0),
    },
    "weekly-synthesis-monday-0700": {
        "task": "atlas.reports.build_weekly",
        "schedule": crontab(hour=7, minute=0, day_of_week=1),
    },
    "vault-reconcile-hourly": {
        "task": "atlas.maintenance.reconcile",
        "schedule": crontab(minute=15),
    },
    "stream-drain-every-2s": {
        "task": "atlas.ingest.drain_stream",
        "schedule": 2.0,
    },
}
