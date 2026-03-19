from django.apps import AppConfig


class VrllogConfig(AppConfig):
    name = 'vrllog'
    default_auto_field = 'django.db.models.BigAutoField'
    
    def ready(self):
        """Initialize app and register signal handlers"""
        import vrllog.signals  # noqa: F401
