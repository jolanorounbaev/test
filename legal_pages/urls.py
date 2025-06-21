from django.urls import path
from . import views

urlpatterns = [
    path('about-me/', views.about_me, name='about_me'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('more-info/', views.more_info, name='more_info'),
]