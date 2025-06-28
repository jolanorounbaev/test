from django.apps import AppConfig
import os


class EventsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'events'
    path = os.path.dirname(os.path.abspath(__file__))
