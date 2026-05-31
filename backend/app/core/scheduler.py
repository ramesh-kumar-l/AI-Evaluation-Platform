"""In-process background scheduler — soft dependency on APScheduler.

Offline-first: if APScheduler is not installed, auto-scheduling is silently disabled.
Manual trigger via POST /observe/schedules/{key}/trigger always works regardless.
"""

from __future__ import annotations

import importlib.util
from typing import Any

from app.core.logging import get_logger

log = get_logger(__name__)

_HAS_APSCHEDULER = importlib.util.find_spec("apscheduler") is not None

_scheduler: Any = None


def configure_scheduler() -> None:
    """Start the background scheduler and register active EvalSchedules."""
    global _scheduler  # noqa: PLW0603

    if not _HAS_APSCHEDULER:
        log.debug("scheduler.disabled", reason="apscheduler not installed")
        return

    from apscheduler.schedulers.background import BackgroundScheduler

    sched = BackgroundScheduler()
    sched.start()
    _scheduler = sched
    _register_active_schedules(sched)
    log.info("scheduler.started")


def stop_scheduler() -> None:
    global _scheduler  # noqa: PLW0603
    if _scheduler is not None:
        try:
            _scheduler.shutdown(wait=False)
        except Exception:
            pass
        _scheduler = None


def _register_active_schedules(sched: Any) -> None:
    """Load all active EvalSchedules from DB and register cron jobs."""
    try:
        from app.core.database import SessionLocal
        from app.models.eval_schedule import EvalSchedule
        from app.services.versioning import list_latest

        with SessionLocal() as db:
            schedules = [s for s in list_latest(db, EvalSchedule) if s.status == "active"]
            for s in schedules:
                _add_cron_job(sched, s.entity_key, s.cron_expr)
        log.info("scheduler.registered", count=len(schedules))
    except Exception as exc:
        log.warning("scheduler.register_failed", error=str(exc))


def _add_cron_job(sched: Any, schedule_entity_key: Any, cron_expr: str) -> None:
    """Add a cron job for a schedule; parses standard 5-field cron expression."""
    try:
        from apscheduler.triggers.cron import CronTrigger

        parts = cron_expr.split()
        if len(parts) != 5:  # noqa: PLR2004
            log.warning("scheduler.invalid_cron", expr=cron_expr)
            return
        minute, hour, day, month, day_of_week = parts
        trigger = CronTrigger(
            minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week
        )
        sched.add_job(
            _run_scheduled_eval,
            trigger=trigger,
            args=[schedule_entity_key],
            id=str(schedule_entity_key),
            replace_existing=True,
        )
    except Exception as exc:
        log.warning("scheduler.add_job_failed", schedule=str(schedule_entity_key), error=str(exc))


def _run_scheduled_eval(schedule_entity_key: Any) -> None:
    """Executed by the background scheduler thread; runs a triggered evaluation."""
    try:
        import uuid

        from app.core.database import SessionLocal
        from app.models.eval_schedule import EvalSchedule
        from app.services.schedule_service import trigger_schedule
        from app.services.versioning import get_latest

        with SessionLocal() as db:
            schedule = get_latest(db, EvalSchedule, uuid.UUID(str(schedule_entity_key)))
            if schedule is not None and schedule.status == "active":
                trigger_schedule(db, schedule=schedule, actor="scheduler")
    except Exception as exc:
        log.error("scheduler.job_failed", schedule=str(schedule_entity_key), error=str(exc))
