from django.views import generic
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth.models import User
from .tasks import import_user_photos
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from .models import Photo, Tag, ExifTag
from django.db.models.aggregates import Count
from .utils import gps_conversion
import json

class IndexView(generic.TemplateView):
    template_name = 'index.html'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('start'))
        return super().dispatch(request, *args, **kwargs)


class StartView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'start.html'


class ResultsView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        custom_user_id = self.request.GET.get('user_id')
        if custom_user_id and self.request.user.is_authenticated and self.request.user.is_staff:
            user = User.objects.get(id=custom_user_id)
        else:
            user = self.request.user
        context['user'] = user
        context['photos'] = Photo.objects.filter(user=user, processed=True).prefetch_related('tags')
        context['tags'] = (
            Tag.objects.filter(user=user)
            .values('description')
            .annotate(count=Count('description'))
            .order_by('-count')
        )
        return context


class StaffMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

    def handle_no_permission(self):
        return HttpResponseRedirect('/')


class AdminView(StaffMixin, generic.TemplateView):
    template_name = 'admin.html'

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
            return HttpResponseRedirect(reverse('hoofkantoor'))

        import_user_photos(user)
        messages.info(request, "Photos imported")
        return HttpResponseRedirect(reverse('hoofkantoor'))


class MapView(LoginRequiredMixin, generic.TemplateView):

    template_name = 'map.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        custom_user_id = self.request.GET.get('user_id')
        if custom_user_id and self.request.user.is_authenticated and self.request.user.is_staff:
            user = User.objects.get(id=custom_user_id)
        else:
            user = self.request.user
        context['user'] = user
        photos = Photo.objects.filter(user=user)
        pins = []
        for photo in photos:
            tag_lat = ExifTag.objects.filter(
                photo_id=photo.id,
                tag='GPSLatitude'
            ).first()
            lat = None if tag_lat is None else tag_lat.pretty
            tag_lng = ExifTag.objects.filter(
                photo_id=photo.id,
                tag='GPSLongitude'
            ).first()
            lng = None if tag_lng is None else tag_lng.pretty

            if lng and lat:
                pins.append({
                    'lat': gps_conversion(lat),
                    'lng': gps_conversion(lng),
                    'url': photo.url_s,
                    'title': photo.title,
                })

        context['pins'] = json.dumps(pins)
        return context
