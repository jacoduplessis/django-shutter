import datetime

from django.core.management.base import BaseCommand

from tagger.fgcv.gps import get_estimate
from tagger.fgcv.models import Photo


class Command(BaseCommand):
    help = 'Import user gpx file.'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int)
        parser.add_argument('gpx')
        parser.add_argument('date')
        parser.add_argument('--noop', action='store_true')

    def handle(self, *args, **options):

        user_id = options.get('user_id')
        gpx_path = options.get('gpx')
        date = options.get('date')

        photos = Photo.objects.filter(user_id=user_id, date_taken=date)
        self.stdout.write(str(len(photos)))
        num_imported = 0

        for photo in photos:
            photo_time = datetime.datetime.combine(photo.date_taken, photo.time_taken)
            estimate = get_estimate(time=photo_time, gpx=gpx_path)
            if estimate is None:
                continue
            else:
                num_imported += 1
                lat, lng, bearing, ele = estimate
                photo.latitude = lat
                photo.longitude = lng
                photo.save()
        self.stdout.write(self.style.SUCCESS(f"Number of photos with new geodata: {num_imported}"))
