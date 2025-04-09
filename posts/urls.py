from django.urls import path
from . import views
from .views import delete_comment, delete_post, delete_reply

urlpatterns = [
    path('', views.post_feed, name='post_feed'),
    path('create/', views.create_post, name='create_post'),
    path('comment/<int:post_id>/', views.add_comment, name='add_comment'),
    path('reply/<int:comment_id>/', views.add_reply, name='add_reply'),
    path('post/delete/<int:post_id>/', delete_post, name='delete_post'),
    path('comment/delete/<int:comment_id>/', delete_comment, name='delete_comment'),
    path('reply/delete/<int:reply_id>/', delete_reply, name='delete_reply'),
    path('post/<int:post_id>/like/', views.toggle_post_like, name='toggle_post_like'),
    path('comment/<int:comment_id>/like/', views.toggle_comment_like, name='toggle_comment_like'),
    path('reply/<int:reply_id>/like/', views.toggle_reply_like, name='toggle_reply_like'),
]
