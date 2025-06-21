from django.urls import path
from . import views

app_name = 'moments'

urlpatterns = [
    path('feed/', views.moment_feed, name='moment_feed'),
    path('create/', views.create_moment, name='create'),
    path('<int:moment_id>/ping/', views.ping_user_into_moment, name='ping_moment_user'),
    path("interest-wordlist/", views.interest_wordlist, name="interest_wordlist"),
    path('<uuid:moment_id>/join/', views.join_moment, name='join_moment'),
    path('moment/<uuid:moment_id>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/reply/', views.add_reply, name='add_reply'),
    path('moment/<uuid:moment_id>/leave/', views.leave_moment, name='leave_moment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('reply/<int:reply_id>/delete/', views.delete_reply, name='delete_reply'),
    path('moment/<uuid:moment_id>/delete/', views.delete_moment, name='delete_moment'),
    path("inline-comments/<uuid:moment_id>/", views.load_comments_inline, name="load_comments_inline"),
    path('react/fire/<uuid:moment_id>/', views.fire_reaction_view, name='fire_reaction'),
    path('react/heart/<uuid:moment_id>/', views.heart_reaction_view, name='heart_reaction'),
    path('react/fire/status/<uuid:moment_id>/', views.check_fire_status, name='check_fire_status'),
    path('flag/<uuid:moment_id>/', views.flag_moment, name='flag_moment'),
]
