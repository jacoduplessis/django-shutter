from django.db import models
from django.conf import settings
from .flickr import get_flickr_api_user_session
from django.contrib.postgres.fields import JSONField


# Create your models here.


class Photo(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='photos')
    flickr_id = models.CharField(max_length=100)
    secret = models.CharField(max_length=100, blank=True)
    title = models.CharField(max_length=300, blank=True)
    flickr_tags = models.CharField(max_length=300, blank=True)
    date_imported = models.DateTimeField(auto_now_add=True)
    date_taken = models.DateField(blank=True, null=True)
    time_taken = models.TimeField(blank=True, null=True)
    processed = models.BooleanField(default=False)
    exif_imported = models.BooleanField(default=False)
    machine_tags = models.CharField(max_length=300, blank=True)
    camera = models.CharField(max_length=300, blank=True)
    lens = models.CharField(max_length=300, blank=True)
    aperture = models.DecimalField(blank=True, null=True, max_digits=5, decimal_places=2)
    exposure = models.CharField(max_length=300, blank=True)
    iso = models.IntegerField(blank=True, null=True)
    latitude = models.DecimalField(blank=True, null=True, max_digits=9, decimal_places=6)
    longitude = models.DecimalField(blank=True, null=True, max_digits=9, decimal_places=6)

    url_sq = models.URLField(blank=True)
    url_t = models.URLField(blank=True)
    url_s = models.URLField(blank=True)
    url_q = models.URLField(blank=True)
    url_m = models.URLField(blank=True)
    url_n = models.URLField(blank=True)
    url_z = models.URLField(blank=True)
    url_c = models.URLField(blank=True)
    url_l = models.URLField(blank=True)
    url_o = models.URLField(blank=True)

    def __str__(self):
        return self.title

    def get_api_data(self, method, api=None, **kwargs):
        if api is None:
            api = get_flickr_api_user_session(self.user)

        r = api.get(method, **kwargs)
        r.raise_for_status()
        return r.json()

    def get_info(self, api=None):
        return self.get_api_data('flickr.photos.getInfo', api, params=dict(photo_id=self.flickr_id))

    def get_exif(self, api=None):
        return self.get_api_data('flickr.photos.getExif', api, params=dict(photo_id=self.flickr_id))

    def update_geodata(self, api=None):
        data = self.get_api_data('flickr.photos.getInfo', api, params=dict(photo_id=self.flickr_id))
        try:
            lat = data['photo']['location']['latitude']
            lng = data['photo']['location']['longitude']
        except KeyError:
            return False
        if not (lat and lng):
            return False
        self.latitude = lat
        self.longitude = lng
        self.save()
        return True

    def tag(self):
        from .google import tag_photo
        tag_photo(self.id)


class Tag(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='tags')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tags')
    description = models.CharField(max_length=100)
    mid = models.CharField(max_length=100)
    score = models.FloatField()
    synced = models.BooleanField(default=False)

    def __str__(self):
        return self.description

    def sync(self, api=None):
        if api is None:
            api = get_flickr_api_user_session(self.user)

        params = {
            'photo_id': self.photo.flickr_id,
            'tags': self.description,
        }
        api.post('flickr.photos.addTags', params=params)
        self.synced = True
        self.save()


class Exif(models.Model):
    photo = models.OneToOneField(Photo, unique=True, on_delete=models.CASCADE, related_name='exif')
    data = JSONField(blank=True, default=dict)

    class Meta:
        verbose_name = 'EXIF'
        verbose_name_plural = 'EXIF'
