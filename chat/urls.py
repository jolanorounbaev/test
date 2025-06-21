from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('modal/', views.chat_modal_content, name='chat_modal_content'),  # For initial load
    path('modal/<int:room_id>/', views.chat_modal_content, name='chat_modal_content_room'),  # For loading specific room
    path('<int:room_id>/', views.chat_home, name='chat_room'),
    path('send/<int:room_id>/', views.send_message, name='send_message'),
    path('delete-message/<int:message_id>/', views.delete_message, name='delete_message'),
    path('create_group_chat/', views.create_group_chat, name='create_group_chat'),
    path('check-blocked-status/', views.check_blocked_status, name='check_blocked_status'),
]
