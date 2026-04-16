from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django_apscheduler.jobstores import DjangoJobStore
import logging

logger = logging.getLogger(__name__)

def start():
    from searchs.services import update_snapshot
    from django.db import connection
    
    if "django_apscheduler_djangojob" not in connection.introspection.table_names():
        logger.warning("django_apscheduler table not found, skipping scheduler start")
        return 
    
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    scheduler.add_job(
        update_snapshot,
        trigger=IntervalTrigger(minutes=1),
        id="update_search_snapshot",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("scheduler started")