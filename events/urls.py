from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.events_home, name='events_home'),
    path('create/', views.create_event, name='create_event'),
    path('delete/<int:event_id>/', views.delete_event, name='delete_event'),
    path('request-join/<int:event_id>/', views.request_join_event, name='request_join_event'),
    path('handle-join/<int:join_request_id>/<str:action>/', views.handle_join_request, name='handle_join_request'),
    path('leave/<int:event_id>/', views.leave_event, name='leave_event'),
    path('quick-nearby/', views.quick_nearby_events, name='quick_nearby_events'),
]
