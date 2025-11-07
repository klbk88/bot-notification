"""Cron scheduler for periodic tasks."""
import asyncio
import logging
from typing import Callable, List, Dict, Any, Optional
import aiocron

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CronScheduler:
    """
    Cron-based task scheduler.

    Uses crontab syntax for scheduling:
    - '*/5 * * * *' - every 5 minutes
    - '0 * * * *' - every hour at minute 0
    - '0 9 * * *' - every day at 9:00 AM
    - '0 9 * * 1' - every Monday at 9:00 AM
    - '*/30 * * * *' - every 30 minutes
    - '0 */2 * * *' - every 2 hours

    Format: minute hour day month day_of_week
    """

    def __init__(self):
        self.jobs: List[aiocron.Cron] = []
        self.is_running = False

    def add_job(self, cron_expression: str, func: Callable, **kwargs) -> aiocron.Cron:
        """
        Add a cron job.

        Args:
            cron_expression: Cron expression (e.g., '*/5 * * * *')
            func: Async function to execute
            **kwargs: Additional arguments to pass to the function

        Returns:
            Cron job instance

        Examples:
            # Every 5 minutes
            scheduler.add_job('*/5 * * * *', my_async_function)

            # Every day at 9 AM
            scheduler.add_job('0 9 * * *', send_daily_report)

            # Every Monday at 10 AM
            scheduler.add_job('0 10 * * 1', weekly_cleanup)
        """
        try:
            job = aiocron.crontab(cron_expression, func=func, args=(), kwargs=kwargs)
            self.jobs.append(job)
            logger.info(f"Added cron job: {cron_expression}")
            return job
        except Exception as e:
            logger.error(f"Failed to add cron job '{cron_expression}': {e}")
            raise

    def remove_job(self, job: aiocron.Cron):
        """Remove a cron job."""
        if job in self.jobs:
            job.stop()
            self.jobs.remove(job)
            logger.info("Removed cron job")

    def start(self):
        """Start all cron jobs."""
        self.is_running = True
        for job in self.jobs:
            job.start()
        logger.info(f"Started {len(self.jobs)} cron jobs")

    def stop(self):
        """Stop all cron jobs."""
        self.is_running = False
        for job in self.jobs:
            job.stop()
        logger.info("Stopped all cron jobs")

    def get_jobs_info(self) -> List[Dict[str, Any]]:
        """Get information about all scheduled jobs."""
        jobs_info = []
        for job in self.jobs:
            jobs_info.append({
                "spec": str(job.spec),
                "running": job.handle is not None
            })
        return jobs_info


class ScheduledNotificationService:
    """
    Notification service with cron scheduling support.

    Supports multiple scheduling strategies:
    - Cron-based scheduling
    - Interval-based polling
    - Immediate processing
    """

    def __init__(self, notification_service):
        self.notification_service = notification_service
        self.scheduler = CronScheduler()

    def schedule_cron(self, cron_expression: str):
        """
        Schedule event processing using cron expression.

        Args:
            cron_expression: Cron expression (e.g., '*/5 * * * *' for every 5 minutes)

        Example:
            service.schedule_cron('*/10 * * * *')  # Every 10 minutes
        """
        self.scheduler.add_job(
            cron_expression,
            self.notification_service.process_events
        )

    def schedule_interval(self, interval_seconds: int):
        """
        Schedule event processing at fixed intervals.

        Args:
            interval_seconds: Interval in seconds

        Example:
            service.schedule_interval(300)  # Every 5 minutes
        """
        # Convert to cron: every N minutes
        minutes = max(1, interval_seconds // 60)
        if minutes == 1:
            cron_expr = "* * * * *"  # Every minute
        else:
            cron_expr = f"*/{minutes} * * * *"

        self.scheduler.add_job(
            cron_expr,
            self.notification_service.process_events
        )
        logger.info(f"Scheduled processing every {minutes} minute(s)")

    def schedule_multiple(self, schedules: List[str]):
        """
        Schedule event processing with multiple cron expressions.

        Args:
            schedules: List of cron expressions

        Example:
            service.schedule_multiple([
                '0 9 * * *',   # Daily at 9 AM
                '0 18 * * *',  # Daily at 6 PM
                '*/30 * * * *' # Every 30 minutes
            ])
        """
        for cron_expr in schedules:
            self.schedule_cron(cron_expr)

    def start(self):
        """Start the scheduler."""
        self.scheduler.start()
        logger.info("Notification scheduler started")

    def stop(self):
        """Stop the scheduler."""
        self.scheduler.stop()
        logger.info("Notification scheduler stopped")

    def get_schedule_info(self) -> Dict[str, Any]:
        """Get information about current schedules."""
        return {
            "jobs": self.scheduler.get_jobs_info(),
            "total_jobs": len(self.scheduler.jobs),
            "is_running": self.scheduler.is_running
        }


# Example configurations
SCHEDULE_PRESETS = {
    "frequent": "*/5 * * * *",      # Every 5 minutes
    "moderate": "*/15 * * * *",     # Every 15 minutes
    "hourly": "0 * * * *",          # Every hour
    "twice_daily": ["0 9 * * *", "0 18 * * *"],  # 9 AM and 6 PM
    "daily": "0 9 * * *",           # Every day at 9 AM
    "weekdays": "0 9 * * 1-5",      # Weekdays at 9 AM
    "weekends": "0 10 * * 0,6",     # Weekends at 10 AM
}


def get_preset_schedule(preset_name: str) -> Optional[str]:
    """
    Get a preset schedule configuration.

    Args:
        preset_name: Name of the preset (frequent, moderate, hourly, etc.)

    Returns:
        Cron expression or None if preset not found
    """
    return SCHEDULE_PRESETS.get(preset_name)
