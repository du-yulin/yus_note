from django.db.models.signals import pre_delete
from django.dispatch import receiver

from user.models import User


@receiver(pre_delete, sender=User)
def user_pre_delete_handler(sender, instance, using, origin, **kwargs):
    """删除用户之前"""
    # 删除用户的私有笔记
    instance.self_notes.filter(is_private=True).delete()
    # 删除根目录
    instance.folders.filter(parent=None).delete()
