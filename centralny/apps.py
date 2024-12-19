from django.apps import AppConfig

# I think this name becomes the leading prefix on the database table names, etc.
class CentralNyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'centralny'
