from django.apps import AppConfig


class UserProxyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_proxy'
    verbose_name = '用户行为'
