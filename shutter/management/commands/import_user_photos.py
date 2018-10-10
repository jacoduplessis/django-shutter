from pprint import pformat

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from shutter.flickr import get_flickr_api_user_session
from shutter.tasks import import_user_photos


class Command(BaseCommand):
    help = 'Import user photos from flickr.'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int)
        parser.add_argument('--print_one', action='store_true')

    def handle(self, *args, **options):

        user_id = options.get('user_id')
        user = User.objects.get(id=user_id)

        if options.get('print_one'):
            flickr_api = get_flickr_api_user_session(user)
            params = {
                'user_id': 'me',
                'per_page': 1,
                'page': 1,
                'content_type': 1,  # photos only
                'extras': 'date_taken,tags,geo,machine_tags,url_sq,url_t,url_s,url_q,url_m,url_n,url_z,url_c,url_l,url_o'
            }
            response = flickr_api.get('flickr.people.getPhotos', params=params).json()
            self.stdout.write(pformat(response, indent=2))
        else:
            import_user_photos(user)

            self.stdout.write(self.style.SUCCESS("Done."))
