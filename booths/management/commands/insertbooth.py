import csv
import os
from django.core.management.base import BaseCommand, CommandError
from utils.helpers import tsv_file
from booths.models import Booth
from searchs.models import Location

class Command(BaseCommand):
    help = """Booth 모델에 여러 개의 레코드를 삽입합니다.
SCP로 EC2에 tsv 파일을 직접 업로드한 후에 명령어를 실행해 주세요."""

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=tsv_file,
            required=True,
            help="tsv 파일 경로를 입력해 주세요.",
        )

    def handle(self, *args, **options):
        file_path:str = options['file']

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                data_list = list(reader)
        except Exception as e:
            raise CommandError(f"tsv 파일을 읽는 중 오류가 발생했습니다: {e}")

        booth_list = list()
        for data in data_list:
            try:
                location = Location.objects.get(
                    building=data['location_building'],
                    number=data['location_number'],
                )
            except Location.DoesNotExist:
                raise CommandError(
                    f"Location 데이터가 올바르지 않습니다. "
                    f"(building={data['location.building']}, number={data['location.number']})"
                )

            booth = Booth(
                id=data['id'],
                name=data['name'],
                schedule=data['schedule'],
                host=data['host'],
                location=location,
            )
            booth.set_admincode(data['admincode'])
            booth_list.append(booth)

        try:
            instances = Booth.objects.bulk_create(booth_list)
        except Exception as e:
            raise CommandError(f"bulk_create 중 오류가 발생했습니다: {e}")

        self.stdout.write(self.style.SUCCESS(f"Booth 모델에 데이터 {len(instances)}개를 삽입했습니다."))

        os.remove(file_path)
        self.stdout.write("tsv 파일을 삭제했습니다.")
