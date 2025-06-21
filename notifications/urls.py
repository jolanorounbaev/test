from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('dropdown/', views.notifications_dropdown, name='notifications_dropdown'),
    path('accept-request/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('decline-request/<int:request_id>/', views.decline_friend_request, name='decline_friend_request'),
    path('unread-count/', views.unread_count, name='unread_count'),
    ]
