from django.apps import AppConfig


class UserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user'
    verbose_name = '用户'

    def ready(self):
        from user.signals import user_pre_delete_handler
