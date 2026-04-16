import argparse
import csv
from django.core.management.base import BaseCommand, CommandError
from utils.choices import LocationChoices
from shows.models import Show
from searchs.models import Location

class Command(BaseCommand):
    help = """Show 모델에 여러 개의 레코드를 삽입합니다.
로컬에 파일을 준비한 뒤, 파일이 존재하는 곳에서 명령어를 실행해 주세요."""

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=argparse.FileType('r'),
            required=True,
            help="tsv 파일 경로를 입력해 주세요.",
        )

    def handle(self, *args, **options):
        file = options['file']
        reader = csv.DictReader(file, delimiter='\t')
        data_list = list(reader)

        show_list = list()
        for data in data_list:
            try:
                location = Location.objects.get(
                    building=LocationChoices.STUDENT_UNION,
                    number__isnull=True,
                )
            except Location.DoesNotExist:
                raise CommandError(
                    f"Location 데이터가 올바르지 않습니다. "
                    f"(building={LocationChoices.STUDENT_UNION}, number=Null)"
                )

            show = Show(
                id=data['id'],
                name=data['name'],
                schedule=data['schedule'],
                location=location,
            )
            show.set_admincode(data['admincode'])
            show_list.append(show)

        try:
            instances = Show.objects.bulk_create(show_list)
        except Exception as e:
            raise CommandError(f"bulk_create 중 오류가 발생했습니다: {e}")

        self.stdout.write(self.style.SUCCESS(f"Show 모델에 데이터 {len(instances)}개를 삽입했습니다."))
