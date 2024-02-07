# Generated by Django 4.2.1 on 2024-01-19 06:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0006_remove_userfolders_user_folders_uni_user_name_par_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usercollections',
            name='last_review_score',
        ),
        migrations.AddField(
            model_name='usercollections',
            name='last_review_feedback',
            field=models.FloatField(blank=True, null=True, verbose_name='最近复习反馈'),
        ),
        migrations.AddField(
            model_name='usercollections',
            name='review_stage',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='复习阶段'),
        ),
    ]
