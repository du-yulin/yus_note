# Generated by Django 4.2.1 on 2024-01-20 16:50

from django.db import migrations, models
import user.models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0010_alter_user_publish_history_alter_user_review_history'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='publish_history',
            field=models.JSONField(blank=True, default=user.models.default_history, help_text="笔记发布记录: 键为日期字符串; 值为每天复习数量, 每天复习数量使用','隔开。", verbose_name='发布记录'),
        ),
        migrations.AlterField(
            model_name='user',
            name='review_history',
            field=models.JSONField(blank=True, default=user.models.default_history, help_text="笔记复习记录: 键为日期字符串; 值为每天复习数量, 每天复习数量使用','隔开。", verbose_name='复习记录'),
        ),
    ]