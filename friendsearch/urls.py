from django.urls import path
from . import views
from .views import edit_interests_inline, autocomplete_view

urlpatterns = [
    path('', views.friend_search_view, name='friend_search'),
    path("edit-interests-inline/", edit_interests_inline, name="edit_interests_inline"),
    path('your-friends/', views.your_friends, name='your_friends'),
    path('autocomplete/', autocomplete_view, name='autocomplete'),
    path('send-friend-request/', views.send_friend_request, name='send_friend_request'),
    path('search-people/', views.search_people, name='search_people'),
    path('remove-friend/<int:friend_id>/', views.remove_friend, name='remove_friend'),
    path('friend-requests-json/', views.friend_requests_json, name='friend_requests_json'),
]
