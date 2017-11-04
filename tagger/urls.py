"""tagger URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/dev/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from tagger.fgcv import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('account/', include('allauth.urls')),
    path('hoofkantoor/', views.AdminView.as_view(), name='hoofkantoor'),
    path('hoofkantoor/import/', views.ImportUserPhotosView.as_view(), name='import_user_photos'),
    path('start/', views.StartView.as_view(), name='start'),
    path('results/', views.ResultsView.as_view(), name='results'),
    path('map/', views.MapView.as_view(), name='map'),
    path('', views.IndexView.as_view(), name='index')

]
