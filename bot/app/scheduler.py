"""
APScheduler setup with SQLAlchemy job store for persistent reminders.
Jobs survive bot container restarts because they are stored in PostgreSQL.
"""
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings

scheduler = AsyncIOScheduler(
    jobstores={
        "default": SQLAlchemyJobStore(url=settings.database_url_sync, tablename="apscheduler_jobs")
    },
    timezone=settings.tz,
    job_defaults={
        "coalesce": True,
        "max_instances": 1,
        "misfire_grace_time": 120,  # fire up to 2 min late if bot was down
    },
)


def add_reminder_job(booking_id: str, telegram_id: int, run_at) -> str:
    """Schedule a reminder 5 minutes before the booking starts."""
    from app.handlers.reminders import send_reminder

    job_id = f"reminder_{booking_id}"
    scheduler.add_job(
        send_reminder,
        trigger="date",
        run_date=run_at,
        args=[booking_id, telegram_id],
        id=job_id,
        replace_existing=True,
    )
    return job_id


def remove_reminder_job(booking_id: str) -> None:
    job_id = f"reminder_{booking_id}"
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass  # Job may have already fired or never existed
