from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
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
    try:
        scheduler.add_job(
            update_snapshot,
            trigger=CronTrigger(minute=0),
            id="update_search_snapshot",
            replace_existing=True,
        )
    except Exception as e:
        # 멀티 워커 환경에서 다른 워커가 먼저 등록한 경우 중복 키 오류가 발생할 수 있음
        logger.warning("Scheduler job registration failed (likely duplicate from another worker): %s", e)
        return
    scheduler.start()
    logger.info("scheduler started")
