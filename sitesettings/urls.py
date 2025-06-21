from django.urls import path
from . import views

urlpatterns = [
    path('', views.site_settings, name='site_settings'),
    path('delete-account/', views.delete_account, name='delete_account'),
]
