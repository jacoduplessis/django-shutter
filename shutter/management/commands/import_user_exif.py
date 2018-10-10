from django.core.management.base import BaseCommand
from shutter.flickr import get_flickr_api_user_session
from django.contrib.auth.models import User
from shutter.models import Photo, Exif
import requests


class Command(BaseCommand):
    help = 'Import exif tags from flickr.'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int)
        parser.add_argument('--limit', type=int)
        parser.add_argument('--photo_id', type=int)

    def handle(self, *args, **options):

        user_id = options.get('user_id')
        limit = options.get('limit')
        user = User.objects.get(id=user_id)
        api_session = get_flickr_api_user_session(user)
        photo_id = options.get('photo_id')
        if photo_id:
            try:
                photo = Photo.objects.get(id=photo_id)
                photos = [photo]
            except Photo.DoesNotExist:
                photos = []
        else:
            photos = Photo.objects.filter(user=user, exif_imported=False)
            if limit:
                photos = photos[:limit]

        for photo in photos:
            params = {
                'photo_id': photo.flickr_id,
            }
            response = api_session.get(
                'flickr.photos.getExif',
                params=params,
            )

            if response.status_code == requests.codes.ok:
                data = response.json()
                camera = data['photo'].get('camera')
                lens = None  # LensModel
                aperture = None  # FNumber
                exposure = None  # ExposureTime
                iso = None  # ISO

                exif_tags = data['photo']['exif']
                exif_data = {}
                for tag in exif_tags:
                    key = tag.get('tag')
                    value = tag.get('raw', {}).get('_content')
                    if key and value:
                        exif_data.update({key: value})

                        # store some import fields on photo itself
                        if key == 'LensModel':
                            lens = value
                        elif key == 'FNumber':
                            aperture = value
                        elif key == 'ExposureTime':
                            exposure = value
                        elif key == 'ISO':
                            iso = value

                Exif.objects.create(photo=photo, data=exif_data)

                photo.camera = camera
                photo.lens = lens
                photo.exposure = exposure
                photo.iso = iso
                photo.aperture = aperture
                photo.exif_imported = True
                photo.save()

        self.stdout.write(self.style.SUCCESS("Number of photos: {}".format(len(photos))))
