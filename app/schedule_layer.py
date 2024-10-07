# schedule_layer.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
from datetime import time as dt_time, datetime, timedelta
from typing import Callable, Optional, Coroutine
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScheduleLayer:
    def __init__(self, timezone: str):
        self._timezone = timezone
        self.first_execution_times = [dt_time(hour, minute) for hour in range(24) for minute in range(0, 60, 15)]
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone(self._timezone))
        logger.info(f"Scheduler initialized with timezone: {self._timezone}")

    def schedule_process_time(self, run_time: datetime, function_to_call: Callable[..., Coroutine], *args):
        timezone = pytz.timezone(self._timezone)
        if run_time.tzinfo is None:
            run_time = timezone.localize(run_time)
        else:
            run_time = run_time.astimezone(timezone)

        self.scheduler.add_job(
            self._run_async_function, 
            'date', 
            run_date=run_time, 
            args=[function_to_call, *args], 
            coalesce=True, 
            misfire_grace_time=30
        )
        logger.info(f"Scheduled '{function_to_call.__name__}' at {run_time} in timezone {self._timezone}")

    def schedule_daily_job(self, hour: int, minute: int, function_to_call: Callable[..., Coroutine], *args):
        self.scheduler.add_job(
            self._run_async_function,
            trigger='cron',
            hour=hour,
            minute=minute,
            args=[function_to_call, *args],
            timezone=self._timezone,
            coalesce=True,
            misfire_grace_time=30
        )
        logger.info(f"Scheduled '{function_to_call.__name__}' daily at {hour:02d}:{minute:02d} in timezone {self._timezone}")

    def schedule_interval_job(
        self, 
        hours: int, 
        function_to_call: Callable[..., Coroutine], 
        start_date: Optional[datetime] = None, 
        *args,
        **kwargs
    ):
        """
        Schedules a job to run at fixed intervals, starting at a specific time.
    
        Args:
            hours (int): Interval in hours.
            function_to_call (Callable[..., Coroutine]): The asynchronous function to schedule.
            start_date (Optional[datetime]): When to start the job. If None, starts immediately.
            *args: Arguments to pass to the function.
        """
        self.scheduler.add_job(
            self._run_async_function,
            trigger='interval',
            hours=hours,
            start_date=start_date,
            args=[function_to_call, *args],
            kwargs=kwargs,
            timezone=self._timezone,
            coalesce=True,
            misfire_grace_time=30
        )
        logger.info(
            f"Scheduled '{function_to_call.__name__}' every {hours} hours "
            f"starting at {start_date} with args {args} and kwargs {kwargs} in timezone {self._timezone}"
        )

    async def _run_async_function(self, function_to_call: Callable[..., Coroutine], *args, **kwargs):
        logger.info(f"Executing function '{function_to_call.__name__}' with args: {args} and kwargs {kwargs}")
        await function_to_call(*args, **kwargs)

    def get_next_execution_time(self, ans: bool = False) -> datetime:
        timezone = pytz.timezone(self._timezone)
        now_datetime = datetime.now(timezone)
        now_time = now_datetime.time()
        sorted_times = sorted(t for t in self.first_execution_times if t > now_time)
        if sorted_times:
            next_time_of_day = sorted_times[1] if ans and len(sorted_times) > 1 else sorted_times[0]
        else:
            next_time_of_day = self.first_execution_times[0]
        
        # Combine current date with next_time_of_day
        naive_datetime = datetime.combine(now_datetime.date(), next_time_of_day)
        
        # Localize the naive datetime to the specified timezone
        next_execution_datetime = timezone.localize(naive_datetime)
        
        # If the scheduled time is in the past, schedule for the next day
        if next_execution_datetime <= now_datetime:
            next_execution_datetime += timedelta(days=1)
        
        return next_execution_datetime

    def stop_all_jobs(self):
        """Stops all scheduled jobs."""
        self.scheduler.remove_all_jobs()
        logger.info("All scheduled jobs have been removed.")

    @property
    def timezone(self):
        return self._timezone
    
    @timezone.setter
    def timezone(self, new_timezone):
        self._timezone = new_timezone