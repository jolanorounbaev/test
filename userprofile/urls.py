from django.urls import path
from .views import profile_view, edit_profile_view, delete_content_item

urlpatterns = [
    path('profile/', profile_view, name='profile'),                          # View own profile
    path('profile/<int:user_id>/', profile_view, name='user_profile'),      # View another user's profile
    path('profile/edit/', edit_profile_view, name='edit_profile'),
    path('delete-content/<int:item_id>/', delete_content_item, name='delete_content'),
]
