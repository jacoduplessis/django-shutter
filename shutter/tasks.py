from datetime import datetime

from .flickr import get_flickr_api_user_session
from .models import Photo, Tag


def import_user_photos(user):
    flickr_api = get_flickr_api_user_session(user)

    def get_and_create(page=1):
        params = {
            'user_id': 'me',
            'per_page': 500,
            'page': page,
            'content_type': 1,  # photos only
            'extras': 'date_taken,tags,geo,machine_tags,url_sq,url_t,url_s,url_q,url_m,url_n,url_z,url_c,url_l,url_o'
        }
        response = flickr_api.get('flickr.people.getPhotos', params=params).json()
        data = response['photos']
        photos = data['photo']
        pages = data['pages']
        current_page = data['page']
        to_create = []
        for photo in photos:
            date_string = photo.get('datetaken')  # 2017-08-12 12:13:12
            date_taken = None
            time_taken = None
            if date_string:
                try:
                    parsed_date = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
                    date_taken = parsed_date.date()
                    time_taken = parsed_date.time()
                except Exception:
                    pass
            to_create.append(Photo(
                user=user,
                title=photo.get('title', ''),
                flickr_id=photo.get('id'),
                secret=photo.get('secret'),
                flickr_tags=photo.get('tags', ''),
                date_taken=date_taken,
                time_taken=time_taken,
                machine_tags=photo.get('machine_tags', ''),
                url_sq=photo.get('url_sq', ''),
                url_t=photo.get('url_t', ''),
                url_s=photo.get('url_s', ''),
                url_q=photo.get('url_q', ''),
                url_m=photo.get('url_m', ''),
                url_n=photo.get('url_n', ''),
                url_z=photo.get('url_z', ''),
                url_c=photo.get('url_c', ''),
                url_l=photo.get('url_l', ''),
                url_o=photo.get('url_o', ''),
                latitude=photo.get('latitude'),
                longitude=photo.get('longitude'),
            ))

        Photo.objects.bulk_create(to_create)
        if current_page < pages:
            get_and_create(current_page + 1)

    get_and_create()


def sync_user_tags(user):
    flickr_api = get_flickr_api_user_session(user)
    qs = Tag.objects.filter(user=user, synced=False).select_related('photo')
    sync_tag_queryset(qs, flickr_api)


def sync_tag_queryset(queryset, flickr_api):
    for tag in queryset:
        params = {
            'photo_id': tag.photo.flickr_id,
            'tags': tag.description,
        }
        flickr_api.post('flickr.photos.addTags', params=params)
        tag.synced = True
        tag.save()
