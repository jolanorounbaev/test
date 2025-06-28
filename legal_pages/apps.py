from django.apps import AppConfig
import os


class LegalPagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'legal_pages'
    path = os.path.dirname(os.path.abspath(__file__))
