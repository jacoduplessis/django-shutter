import datetime

from django.core.management.base import BaseCommand

from shutter.gps import get_estimate, get_lat_lon_time_from_gpx
from shutter.models import Photo


class Command(BaseCommand):
    help = 'Import user gpx file.'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int)
        parser.add_argument('gpx')
        parser.add_argument('--offset', type=int)
        parser.add_argument('--noop', action='store_true')

    def handle(self, *args, **options):

        user_id = options.get('user_id')
        gpx_path = options.get('gpx')
        offset = options.get('offset')
        points = get_lat_lon_time_from_gpx(gpx_path)
        start_date = points[0][0].date()
        end_date = points[-1][0].date()
        self.stdout.write(str(start_date))
        self.stdout.write(str(end_date))
        photos = Photo.objects.filter(user_id=user_id, date_taken__gte=start_date, date_taken__lte=end_date)
        self.stdout.write(str(len(photos)))
        num_imported = 0

        for photo in photos:
            photo_time = datetime.datetime.combine(photo.date_taken, photo.time_taken)
            if offset:
                photo_time += datetime.timedelta(hours=offset)
            estimate = get_estimate(time=photo_time, points=points)
            if estimate is None:
                continue
            else:
                num_imported += 1
                lat, lng, bearing, ele = estimate
                photo.latitude = lat
                photo.longitude = lng
                photo.save()

        self.stdout.write(self.style.SUCCESS(f"Number of photos with new geodata: {num_imported}"))
