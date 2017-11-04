from django.core.management.base import BaseCommand
from requests_futures.sessions import FuturesSession
from tagger.fgcv.flickr import get_flickr_api_user_session
from django.contrib.auth.models import User
import requests


class Command(BaseCommand):
    help = 'Write tags back to flickr.'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int)

    def handle(self, *args, **options):

        user_id = options.get('user_id')
        user = User.objects.get(id=user_id)
        session = get_flickr_api_user_session(user)
        tags = user.tags.filter(synced=False).select_related('photo')

        def callback_factory(tag):
            def wrapper(session, response):
                if response.status_code == requests.codes.ok:
                    tag.synced = True
                    tag.save()

            return wrapper

        with FuturesSession(session=session, max_workers=50) as api:
            futures = []

            for tag in tags:
                params = {
                    'photo_id': tag.photo.flickr_id,
                    'tags': tag.description,
                }
                future = api.post(
                    'flickr.photos.addTags',
                    params=params,
                    background_callback=callback_factory(tag)
                )
                futures.append(future)

        self.stdout.write(self.style.SUCCESS("Number of tags: {}".format(len(tags))))
