from django.apps import AppConfig

# I think this name becomes the leading prefix on the database table names, etc.
class MarkersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'centralny'
