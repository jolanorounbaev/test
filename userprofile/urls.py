from django.urls import path
from .views import profile_view, edit_profile_view, delete_content_item, report_user, block_user, blocked_users_list
from . import views
from .views import get_word_list_api # Add this import

urlpatterns = [
    path('profile/', profile_view, name='profile'),                          # View own profile
    path('profile/<int:user_id>/', profile_view, name='user_profile'),      # View another user's profile
    path('profile/edit/', edit_profile_view, name='edit_profile'),
    path('delete-content/<int:item_id>/', delete_content_item, name='delete_content'),
    path('profile/place/delete/<int:place_id>/', views.delete_place, name='delete_place'),
    path('api/get_word_list/', get_word_list_api, name='get_word_list_api'), # Add this line    path('profile/remove_picture/', views.remove_profile_picture, name='remove_profile_picture'),
    path('profile/achievement/delete/<int:achievement_id>/', views.delete_achievement, name='delete_achievement'),  # New line for deleting achievement
    path('profile/quote/delete/<int:quote_id>/', views.delete_quote, name='delete_quote'),  # New line for deleting quote
    path('report-user/', report_user, name='report_user'),  # Add report functionality
    path('block-user/', block_user, name='block_user'),  # Add block functionality
    path('blocked-users/', blocked_users_list, name='blocked_users_list'),  # View blocked users
]
