from django.core.management.base import BaseCommand
from requests_futures.sessions import FuturesSession
from tagger.fgcv.flickr import get_flickr_api_user_session
from django.contrib.auth.models import User
from tagger.fgcv.models import ExifTag, Photo
import requests


class Command(BaseCommand):
    help = 'Import exif tags from flickr.'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int)
        parser.add_argument('--limit', type=int)

    def handle(self, *args, **options):

        user_id = options.get('user_id')
        limit = options.get('limit')
        user = User.objects.get(id=user_id)
        session = get_flickr_api_user_session(user)
        photos = Photo.objects.filter(user=user, exif_imported=False)
        if limit:
            photos = photos[:limit]

        def callback_factory(photo):
            def wrapper(session, response):
                if response.status_code == requests.codes.ok:
                    data = response.json()
                    to_create = []
                    camera = data['photo'].get('camera', '')
                    exif_tags = data['photo']['exif']
                    for tag in exif_tags:
                        to_create.append(
                            ExifTag(
                                photo=photo,
                                label=tag.get('label', ''),
                                pretty=tag.get('clean', {}).get('_content', ''),
                                raw=tag.get('raw', {}).get('_content', ''),
                                tag=tag.get('tag', ''),
                                tagspace=tag.get('tagspace', '')
                            )
                        )
                    ExifTag.objects.bulk_create(to_create)

                    photo.camera = camera
                    photo.exif_imported = True
                    photo.save()

            return wrapper

        with FuturesSession(session=session, max_workers=50) as api:
            futures = []

            for photo in photos:
                params = {
                    'photo_id': photo.flickr_id,
                }
                future = api.get(
                    'flickr.photos.getExif',
                    params=params,
                    background_callback=callback_factory(photo)
                )
                futures.append(future)

        self.stdout.write(self.style.SUCCESS("Number of photos: {}".format(len(photos))))
