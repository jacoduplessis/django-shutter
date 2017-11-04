from django.core.management.base import BaseCommand
from tagger.fgcv.tasks import import_user_photos
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Import user photos from flickr.'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int)

    def handle(self, *args, **options):

        user_id = options.get('user_id')
        user = User.objects.get(id=user_id)
        import_user_photos(user)

        self.stdout.write(self.style.SUCCESS("Done."))
