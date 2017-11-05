import json

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models.aggregates import Count
from django.http import HttpResponseRedirect
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
    template_name = 'index.html'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('start'))
        return super().dispatch(request, *args, **kwargs)


class StartView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'start.html'


class ResultsView(LoginRequiredMixin, UserOverrideMixin, generic.ListView):
    template_name = 'results.html'
    model = Photo
    paginate_by = 50
    context_object_name = 'photos'

    def get_queryset(self):
        return (Photo.objects
                .filter(user=self.user, processed=True)
                .prefetch_related('tags')
                .order_by('-date_taken', '-time_taken')
                )


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


class MapView(LoginRequiredMixin, UserOverrideMixin, generic.TemplateView):
    template_name = 'map.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.user
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


class TagsView(LoginRequiredMixin, UserOverrideMixin, generic.ListView):
    template_name = 'tags.html'
    context_object_name = 'tags'

    def get_queryset(self):
        return (
            Tag.objects.filter(user=self.user)
                .values('description')
                .annotate(count=Count('description'))
                .order_by('-count')
        )


class GearView(LoginRequiredMixin, UserOverrideMixin, generic.TemplateView):
    template_name = 'gear.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lenses'] = Photo.objects.filter(user=self.user).values('lens').annotate(count=Count('lens')).order_by('-count')
        context['cameras'] = Photo.objects.filter(user=self.user).values('camera').annotate(count=Count('camera')).order_by('-count')
        return context
