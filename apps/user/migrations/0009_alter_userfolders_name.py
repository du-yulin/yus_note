# Generated by Django 4.2.1 on 2024-01-19 16:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0008_alter_usercollections_last_review_feedback'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userfolders',
            name='name',
            field=models.CharField(max_length=32, verbose_name='名称'),
        ),
    ]