from django.apps import AppConfig

class BoothsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'booths'

    def ready(self):
        from .scheduler import start
        start()
