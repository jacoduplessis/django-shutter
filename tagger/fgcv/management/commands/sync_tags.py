from django.core.management.base import BaseCommand
from requests_futures.sessions import FuturesSession
from tagger.fgcv.flickr import get_flickr_api, get_user_oauth, get_flickr_app
from django.contrib.auth.models import User
import requests


class Command(BaseCommand):
    help = 'Import countries from the django_countries app.'

    def handle(self, *args, **options):

        url = 'https://api.flickr.com/services/rest/'
        app = get_flickr_app()
        user = User.objects.get(id=2)
        # session = get_flickr_api(user)
        oauth = get_user_oauth(app=app, user=user)
        session = requests.Session()
        tags = user.tags.filter(synced=False).select_related('photo')

        def callback_factory(tag):
            def wrapper(session, response):
                if response.status_code == requests.codes.ok:
                    tag.synced = True
                    tag.save()

            return wrapper

        with FuturesSession(session=session, max_workers=10) as api:
            futures = []

            for tag in tags:
                params = {
                    'photo_id': tag.photo.flickr_id,
                    'tags': tag.description,
                    'method': 'flickr.photos.addTags',
                    'api_key': app.client_id,
                    'format': 'json',
                    'nojsoncallback': 1,
                }
                future = api.post(
                    url,
                    params=params,
                    auth=oauth,
                    background_callback=callback_factory(tag)
                )
                futures.append(future)

        self.stdout.write(self.style.SUCCESS("Number of tags: {}".format(len(tags))))
