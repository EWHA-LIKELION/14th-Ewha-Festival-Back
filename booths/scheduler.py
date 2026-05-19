from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from django_apscheduler.jobstores import DjangoJobStore

def start():
    from .models import Booth # 순환 참조 방지
    from .services import BoothService

    scheduler = BackgroundScheduler(timezone="Asia/Seoul")
    scheduler.add_jobstore(DjangoJobStore(), "default")

    booth_service = BoothService(booth_model=Booth)
    reset_all = dict(
        func=booth_service.reset_all,
        replace_existing=True,
    )

    scheduler.add_job(
        **reset_all,
        trigger=CronTrigger(hour=0, minute=0),
        id="reset_booth_ongoing_daily_0000",
        name="매일 0시 초기화",
    )
    scheduler.add_job(
        **reset_all,
        trigger=DateTrigger(
            run_date=datetime(2026,5,20,18,0,0),
            timezone="Asia/Seoul"
        ),
        id="reset_booth_ongoing_20260520_1800",
        name="2026.05.20.(수) 18:00 초기화",
    )
    scheduler.add_job(
        **reset_all,
        trigger=DateTrigger(
            run_date=datetime(2026,5,21,18,0,0),
            timezone="Asia/Seoul"
        ),
        id="reset_booth_ongoing_20260521_1800",
        name="2026.05.21.(목) 18:00 초기화",
    )
    scheduler.add_job(
        **reset_all,
        trigger=DateTrigger(
            run_date=datetime(2026,5,22,16,0,0),
            timezone="Asia/Seoul"
        ),
        id="reset_booth_ongoing_20260522_1600",
        name="2026.05.22.(금) 16:00 초기화",
    )

    scheduler.start()
