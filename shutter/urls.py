from django.urls import path
from . import views

urlpatterns = [
    path('hoofkantoor/', views.AdminView.as_view(), name='hoofkantoor'),
    path('hoofkantoor/import/', views.ImportUserPhotosView.as_view(), name='import_user_photos'),
    path('start/', views.StartView.as_view(), name='start'),
    path('results/', views.ResultsView.as_view(), name='results'),
    path('map/', views.MapView.as_view(), name='map'),
    path('tags/', views.TagsView.as_view(), name='tags'),
    path('gear/', views.GearView.as_view(), name='gear'),
    path('photo/update/', views.UpdatePhotoView.as_view(), name='photo_update'),
    path('share/<int:user_id>/', views.MapShareView.as_view(), name='share'),
    path('gallery/', views.GalleryView.as_view(), name='gallery'),
    path('', views.IndexView.as_view(), name='index'),
]

app_name = 'shutter'
