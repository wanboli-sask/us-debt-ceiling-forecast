"""Run: python scheduler.py — starts background daily updates at 16:30 ET."""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from jobs.daily_update import run_daily_update

scheduler = BlockingScheduler()


def job():
    print("Running daily debt ceiling forecast update...")
    result = run_daily_update()
    print(f"Done. X-date estimate: {result['xdate']['x_date_p50']}")


if __name__ == "__main__":
    scheduler.add_job(job, CronTrigger(hour=16, minute=30, timezone="America/New_York"))
    print("Scheduler started. Daily update at 16:30 ET.")
    scheduler.start()
