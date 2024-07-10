# scheduler.py
import os
import json
from datetime import datetime, timedelta
import aiofiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
# Make sure this import path is correct
from tasks.create_clusters import create_clusters

TASKS_METADATA_FILE = "/app/tmp/create_clusters.json"


async def get_initial_delay():
    # Calculate initial delay based on the last run time stored in a JSON file
    if os.path.exists(TASKS_METADATA_FILE):
        async with aiofiles.open(TASKS_METADATA_FILE, 'r') as f:
            metadata = json.loads(await f.read())
        last_run = datetime.fromisoformat(metadata["last_run"])
        now = datetime.now()
        elapsed = now - last_run
        delay = max(0, (timedelta(days=3) - elapsed).total_seconds())
        return delay
    return 0


async def update_last_run_time():
    # Update the last run time in the JSON file asynchronously
    os.makedirs("/app/tmp", exist_ok=True)
    metadata = {"last_run": datetime.now().isoformat()}
    async with aiofiles.open(TASKS_METADATA_FILE, 'w') as f:
        await f.write(json.dumps(metadata))


async def scheduled_task():
    # The task you want to run
    await create_clusters()
    await update_last_run_time()


async def start_scheduler():
    # Start the scheduler and schedule tasks
    scheduler = AsyncIOScheduler()
    initial_delay = await get_initial_delay()
    scheduler.add_job(scheduled_task, IntervalTrigger(
        seconds=initial_delay, days=3))
    scheduler.start()
    print(f"Scheduler started with initial delay of {initial_delay} seconds.")
