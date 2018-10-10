from django.core.management.base import BaseCommand
from shutter.flickr import get_flickr_api_user_session
from django.contrib.auth.models import User
import requests


class Command(BaseCommand):
    help = 'Write tags back to flickr.'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int)

    def handle(self, *args, **options):

        user_id = options.get('user_id')
        user = User.objects.get(id=user_id)
        api_session = get_flickr_api_user_session(user)
        tags = user.tags.filter(synced=False).select_related('photo')

        for tag in tags:
            params = {
                'photo_id': tag.photo.flickr_id,
                'tags': tag.description,
            }
            response = api_session.post(
                'flickr.photos.addTags',
                params=params,
            )
            if response.status_code == requests.codes.ok:
                tag.synced = True
                tag.save()

        self.stdout.write(self.style.SUCCESS("Number of tags: {}".format(len(tags))))
