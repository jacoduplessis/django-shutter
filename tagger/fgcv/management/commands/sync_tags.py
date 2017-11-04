from django.core.management.base import BaseCommand
from requests_futures.sessions import FuturesSession
from tagger.fgcv.flickr import get_user_oauth, get_flickr_app
from django.contrib.auth.models import User
import requests


class Command(BaseCommand):
    help = 'Write tags back to flickr.'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int)

    def handle(self, *args, **options):

        url = 'https://api.flickr.com/services/rest/'
        app = get_flickr_app()
        user_id = options.get('user_id')
        user = User.objects.get(id=user_id)
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
