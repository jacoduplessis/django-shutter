import json

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models.aggregates import Count
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from .models import Photo, Tag
from .tasks import import_user_photos


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

        photos = Photo.objects.filter(user=user, latitude__isnull=False, longitude__isnull=False)
        pins = []
        for photo in photos:
            pins.append({
                'lat': str(photo.latitude),
                'lng': str(photo.longitude),
                'url': photo.url_s,
                'title': photo.title,
            })

        context['pins'] = json.dumps(pins)
        return context
