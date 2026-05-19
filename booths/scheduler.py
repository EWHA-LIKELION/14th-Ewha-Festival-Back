from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from django_apscheduler.jobstores import DjangoJobStore

def start():
    from .services import reset_ongoing

    scheduler = BackgroundScheduler(timezone="Asia/Seoul")
    scheduler.add_jobstore(DjangoJobStore(), "default")

    common = dict(
        func=reset_ongoing,
        replace_existing=True,  # 재시작 시 중복 등록 방지
    )

    scheduler.add_job(
        **common,
        trigger=CronTrigger(hour=0, minute=0),
        id="reset_booth_ongoing_daily_0000",
        name="매일 0시 초기화",
    )
    scheduler.add_job(
        **common,
        trigger=DateTrigger(
            run_date=datetime(2026,5,20,18,0,0),
            timezone="Asia/Seoul"
        ),
        id="reset_booth_ongoing_20260520_1800",
        name="2026.05.20.(수) 18:00 초기화",
    )
    scheduler.add_job(
        **common,
        trigger=DateTrigger(
            run_date=datetime(2026,5,21,18,0,0),
            timezone="Asia/Seoul"
        ),
        id="reset_booth_ongoing_20260521_1800",
        name="2026.05.21.(목) 18:00 초기화",
    )
    scheduler.add_job(
        **common,
        trigger=DateTrigger(
            run_date=datetime(2026,5,22,16,0,0),
            timezone="Asia/Seoul"
        ),
        id="reset_booth_ongoing_20260522_1600",
        name="2026.05.22.(금) 16:00 초기화",
    )

    scheduler.start()
