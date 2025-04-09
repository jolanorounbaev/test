from django.urls import path
from . import views

urlpatterns = [
    path('', views.site_settings, name='site_settings'),
]
