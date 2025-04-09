from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('dropdown/', views.notifications_dropdown, name='notifications_dropdown'),
    path('friend-requests/', views.friend_requests, name='friend_requests'),
    path('send-request/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('accept-request/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('reject-request/<int:request_id>/', views.reject_friend_request, name='reject_friend_request'),
    path('mark-as-read/<int:notification_id>/', views.mark_notification_as_read, name='mark_as_read'),
    path('unread-count/', views.unread_count, name='unread_count'),
    path('mark-as-seen/', views.mark_as_seen, name='mark_as_seen'),
    ]
