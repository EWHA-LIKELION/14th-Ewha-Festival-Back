from django.core.management.base import BaseCommand
from utils.choices import LocationChoices
from searchs.models import Location

class Command(BaseCommand):
    help = """Location 모델에 여러 개의 레코드를 삽입합니다.
삽입하는 레코드의 수는 --kind 값과 --booth-max-number 값에 따라 계산합니다.
building 필드는 --building 값을 모든 레코드에 동일하게 저장하고,
number 필드는 --kind 값과 --booth-max-number 값에 따라 각 레코드를 다르게 처리합니다."""

    def add_arguments(self, parser):
        parser.add_argument(
            '--building',
            type=str,
            choices=LocationChoices.values,
            required=True,
            help="Location 모델의 building 필드에 저장할 값을 입력해 주세요.",
        )
        parser.add_argument(
            '--kind',
            type=str.lower,
            choices=('booth','show',),
            required=True,
        )
        parser.add_argument(
            '--booth-max-number',
            type=int,
            required=False,
            help="해당 구역의 마지막 부스 번호를 입력해 주세요.",
        )

    def handle(self, *args, **options):
        building = options['building']
        kind = options['kind']
        booth_max_number = options['booth_max_number']

        number_list = range(1, booth_max_number+1, 1) if kind == 'booth' else (None,)

        instances = Location.objects.bulk_create([
            Location(building=building, number=number)
            for number in number_list
        ])

        self.stdout.write(self.style.SUCCESS(f"Location 모델에 {LocationChoices(building).label} 구역 데이터 {len(instances)}개를 삽입했습니다."))
