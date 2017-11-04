from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Photo, Tag
from .google import tag_photo_queryset


# Register your models here.


class PhotoAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'processed',
        'user',
        'flickr_tags',
        'date_taken',
        'time_taken',
    ]
    readonly_fields = [
        'user',
        'title',
        'flickr_id',
        'flickr_tags',
        'secret',
        'machine_tags',
        'date_imported',
        'date_taken',
        'time_taken',
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
        'thumbnail',
        'display_tags',
    ]
    list_select_related = ['user']
    date_hierarchy = 'date_taken'
    list_filter = ['user', 'processed']
    ordering = ['-date_taken', '-time_taken']
    actions = ['tag_photos']
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

    def tag_photos(self, request, queryset):
        tag_photo_queryset(queryset)
        self.message_user(request, "{} photos tagged.".format(queryset.count()))


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


admin.site.register(Photo, PhotoAdmin)
admin.site.register(Tag, TagAdmin)
