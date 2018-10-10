from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Photo, Tag, Exif
from .google import tag_photo_queryset
from pprint import pformat


class PhotoAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'processed',
        'exif_imported',
        'user',
        'flickr_tags',
        'date_taken',
        'time_taken',
        'camera',
        'lens',

    ]
    readonly_fields = [
        'thumbnail',
        'user',
        'title',
        'flickr_id',
        'processed',
        'exif_imported',
        'flickr_tags',
        'secret',
        'machine_tags',
        'date_imported',
        'date_taken',
        'time_taken',
        'aperture',
        'exposure',
        'lens',
        'camera',
        'iso',
        'latitude',
        'longitude',
        'url_sq',
        'url_t',
        'url_s',
        'url_q',
        'url_m',
        'url_n',
        'url_z',
        'url_c',
        'url_l',
        'url_o',
        'display_tags',
        'display_exif',
    ]
    list_select_related = ['user']
    date_hierarchy = 'date_taken'
    list_filter = [
        'user',
        'processed',
        'exif_imported',
        'camera',
        'lens',
        'date_taken',
        'latitude',
        'longitude',
    ]
    ordering = [
        '-date_taken',
        '-time_taken'
    ]
    actions = [
        'tag_photos',
        'set_processed_false',
        'set_exif_imported_false',
        'update_geodata'
    ]
    search_fields = ['title']

    def thumbnail(self, obj):
        return mark_safe('<img src="{}">'.format(obj.url_s))

    def display_tags(self, obj):
        tags = obj.tags.all()
        html = '<ul>'
        for tag in tags:
            html += '<li>{} - {}</li>'.format(tag.description, tag.score)
        html += '</ul>'
        return mark_safe(html)

    def display_exif(self, obj):
        if obj.exif:
            return pformat(obj.exif.data)

    def tag_photos(self, request, queryset):
        tag_photo_queryset(queryset)
        self.message_user(request, "{} photos tagged.".format(queryset.count()))

    def set_processed_false(self, request, queryset):
        num = queryset.update(processed=False)
        self.message_user(request, f"{num} photos marked as unprocessed.")

    def set_exif_imported_false(self, request, queryset):
        num = queryset.update(exif_imported=False)
        self.message_user(request, f"{num} photos tagged.")

    def update_geodata(self, request, queryset):
        num = 0
        for photo in queryset:
            updated = photo.update_geodata()
            if updated:
                num += 1
        self.message_user(request, f"{num} geo updated")


class TagAdmin(admin.ModelAdmin):
    list_display = [
        'description',
        'mid',
        'synced',
        'user',
        'photo_id'

    ]
    list_select_related = ['user']
    actions = ['sync_tags', 'mark_synced']
    list_filter = ['synced', 'user']
    search_fields = ['description', 'mid']

    def sync_tags(self, request, queryset):
        for tag in queryset.filter(synced=False):
            tag.sync()
        self.message_user(request, "{} tags synced.".format(queryset.count()))

    def mark_synced(self, request, queryset):
        queryset.update(synced=True)
        self.message_user(request, "{} tags marked as synced.".format(queryset.count()))


class ExifAdmin(admin.ModelAdmin):
    list_display = ['photo']
    list_select_related = ['photo']
    readonly_fields = ['photo', 'data']


admin.site.register(Photo, PhotoAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Exif, ExifAdmin)
