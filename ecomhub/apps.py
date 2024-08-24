from django.apps import AppConfig


class EcomhubConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ecomhub'
    
    def ready(self):
        import ecomhub.signals