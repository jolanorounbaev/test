from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_index, name='chat_index'),  # for /chat/
    path('<str:mode>/<int:id>/', views.chat_room, name='chat_room'),  # for /chat/private/2 or /chat/group/3
]
