from django.apps import AppConfig

class SitesettingsConfig(AppConfig):  # You can rename this class too if you want
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sitesettings'  # ✅ must match the app folder name
