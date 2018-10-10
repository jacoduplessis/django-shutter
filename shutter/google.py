import requests
from .models import Photo, Tag
import os


def tag_photo_queryset(queryset):
    session = requests.session()
    for photo in queryset:
        tag_photo(photo.id, session)


def tag_photo(photo_id, session=None):
    try:
        photo = Photo.objects.get(id=photo_id)
    except Photo.DoesNotExist:
        return
    if session is None:
        session = requests.session()

    url = photo.url_m

    url = url.replace('https://', 'http://')

    payload = {
        "requests": [
            {
                "image": {
                    "source": {
                        "imageUri": url
                    }
                },
                "features": {
                    "type": "LABEL_DETECTION",
                },
            }

        ]
    }
    key = os.environ.get('GOOGLE_CLOUD_KEY', None)
    if key is None:
        raise RuntimeError("Google API key not configured")
    params = {
        'key': key
    }
    r = session.post('https://vision.googleapis.com/v1/images:annotate', json=payload, params=params)
    r.raise_for_status()
    data = r.json()
    labels = data['responses'][0]['labelAnnotations']
    to_create = []
    for label in labels:
        to_create.append(
            Tag(
                photo=photo,
                user_id=photo.user_id,
                description=label.get('description', ''),
                mid=label.get('mid', ''),
                score=label.get('score', 0)
            )
        )
    Tag.objects.bulk_create(to_create)
    photo.processed = True
    photo.save()
