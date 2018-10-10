import json

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Prefetch
from django.db.models.aggregates import Count
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.urls import reverse
from django.utils.functional import cached_property
from django.views import generic

from .models import Photo, Tag
from .tasks import import_user_photos


class StaffMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

    def handle_no_permission(self):
        return HttpResponseRedirect('/')


class UserOverrideMixin:
    @cached_property
    def user(self):
        custom_user_id = self.request.GET.get('user_id')
        if custom_user_id and self.request.user.is_authenticated and self.request.user.is_staff:
            user = User.objects.get(id=custom_user_id)
        else:
            user = self.request.user
        return user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.user
        return context


class IndexView(generic.TemplateView):
    template_name = 'shutter/index.html'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('shutter:start'))
        return super().dispatch(request, *args, **kwargs)


class StartView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'shutter/start.html'


class ResultsView(LoginRequiredMixin, UserOverrideMixin, generic.ListView):
    template_name = 'shutter/results.html'
    model = Photo
    paginate_by = 50
    context_object_name = 'photos'

    def get_queryset(self):
        tags_prefetch = Prefetch(
            'tags',
            queryset=Tag.objects.order_by('-score')
        )

        return (Photo.objects
                .filter(user=self.user, processed=True)
                .prefetch_related(tags_prefetch)
                .order_by('-date_taken', '-time_taken')
                )


class AdminView(StaffMixin, generic.TemplateView):
    template_name = 'shutter/admin.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tags'] = (
            Tag.objects.all()
                .values('description')
                .annotate(count=Count('description'))
                .order_by('-count')
        )
        return context


class ImportUserPhotosView(StaffMixin, generic.View):
    def post(self, request):
        user_id = request.POST.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, "No such user")
            return HttpResponseRedirect(reverse('shutter:hoofkantoor'))

        import_user_photos(user)
        messages.info(request, "Photos imported")
        return HttpResponseRedirect(reverse('shutter:hoofkantoor'))


class TagsView(LoginRequiredMixin, UserOverrideMixin, generic.ListView):
    template_name = 'shutter/tags.html'
    context_object_name = 'tags'

    def get_queryset(self):
        return (
            Tag.objects.filter(user=self.user)
                .values('description')
                .annotate(count=Count('description'))
                .order_by('-count')
        )


class GearView(LoginRequiredMixin, UserOverrideMixin, generic.TemplateView):
    template_name = 'shutter/gear.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lenses'] = Photo.objects.filter(user=self.user).values('lens').annotate(count=Count('lens')).order_by(
            '-count')
        context['cameras'] = Photo.objects.filter(user=self.user).values('camera').annotate(
            count=Count('camera')).order_by('-count')
        return context


class UpdatePhotoView(LoginRequiredMixin, generic.View):
    def post(self, request):

        data = json.loads(self.request.body)
        photo_id = data.get('id')
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if not all([photo_id, latitude, longitude]):
            return HttpResponseBadRequest()

        photo = Photo.objects.get(id=photo_id)

        if not (self.request.user.is_staff or self.request.user.id == photo.user_id):
            return HttpResponseForbidden()

        photo.latitude = latitude
        photo.longitude = longitude
        photo.save()

        return JsonResponse({'updated': True})


class BaseMapView(generic.TemplateView):
    template_name = 'shutter/map.html'

    def get_photos(self, user):
        return (
            Photo.objects
                .filter(user=user, latitude__isnull=False, longitude__isnull=False)
                .prefetch_related('tags')
                .order_by('-date_taken', '-time_taken')
        )

    def get_pins(self, user):
        photos = self.get_photos(user)
        pins = []
        for photo in photos:
            pins.append({
                'id': photo.id,
                'lat': str(photo.latitude),
                'lng': str(photo.longitude),
                'url': photo.url_m,
                'title': photo.title,
                'date': str(photo.date_taken),
                'time': str(photo.time_taken),
            })
        return pins

    def get_tags(self, user):
        tags = (Tag.objects.filter(user=user)
        .values('description')
        .annotate(count=Count('description'))
        .order_by('-count')
                )

        return tags


class MapView(LoginRequiredMixin, UserOverrideMixin, BaseMapView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pins'] = json.dumps(self.get_pins(self.user))
        context['mode'] = 'edit'
        return context


class MapShareView(BaseMapView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        share_id = kwargs.get('user_id')
        if not share_id:
            return HttpResponseRedirect('/')
        user = User.objects.get(id=share_id)
        context['pins'] = json.dumps(self.get_pins(user), indent=2)
        context['mode'] = 'share'

        return context


class GalleryView(LoginRequiredMixin, UserOverrideMixin, generic.ListView):

    model = Photo
    paginate_by = 20
    template_name = 'shutter/gallery.html'
    context_object_name = 'photos'

    def get_queryset(self):
        return Photo.objects.filter(user=self.user)
