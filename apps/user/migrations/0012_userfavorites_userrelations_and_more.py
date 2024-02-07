# Generated by Django 4.2.1 on 2024-01-23 16:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('note', '0006_alter_note_folder'),
        ('user', '0011_alter_user_publish_history_alter_user_review_history'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserFavorites',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, verbose_name='名称')),
            ],
            options={
                'verbose_name': '用户收藏夹',
                'verbose_name_plural': '用户收藏夹',
                'db_table': 'user_user_favarites',
            },
        ),
        migrations.CreateModel(
            name='UserRelations',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': '用户关系',
                'verbose_name_plural': '用户关系',
                'db_table': 'user_user_relations',
            },
        ),
        migrations.RemoveConstraint(
            model_name='userfolders',
            name='user_folders_uni_name_par',
        ),
        migrations.RemoveField(
            model_name='user',
            name='subscriptions',
        ),
        migrations.RemoveField(
            model_name='usercollections',
            name='folder',
        ),
        migrations.RemoveField(
            model_name='userfolders',
            name='collected_notes',
        ),
        migrations.RemoveField(
            model_name='userfolders',
            name='is_private',
        ),
        migrations.AddConstraint(
            model_name='userfolders',
            constraint=models.UniqueConstraint(fields=('name', 'parent'), name='user_folders_uni_name_parent'),
        ),
        migrations.AddField(
            model_name='userrelations',
            name='follower',
            field=models.ForeignKey(limit_choices_to={'is_active': True}, on_delete=django.db.models.deletion.CASCADE, related_name='rel_following', to=settings.AUTH_USER_MODEL, verbose_name='用户'),
        ),
        migrations.AddField(
            model_name='userrelations',
            name='following',
            field=models.ForeignKey(limit_choices_to={'is_active': True}, on_delete=django.db.models.deletion.CASCADE, related_name='rel_followers', to=settings.AUTH_USER_MODEL, verbose_name='被关注用户'),
        ),
        migrations.AddField(
            model_name='userfavorites',
            name='notes',
            field=models.ManyToManyField(blank=True, related_name='favorites', through='user.UserCollections', to='note.note', verbose_name='收藏笔记'),
        ),
        migrations.AddField(
            model_name='userfavorites',
            name='user',
            field=models.ForeignKey(limit_choices_to={'is_active': True}, on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to=settings.AUTH_USER_MODEL, verbose_name='用户'),
        ),
        migrations.AddField(
            model_name='user',
            name='following',
            field=models.ManyToManyField(blank=True, related_name='followers', through='user.UserRelations', to=settings.AUTH_USER_MODEL, verbose_name='关注'),
        ),
        migrations.AddField(
            model_name='usercollections',
            name='favorite',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='collections', to='user.userfavorites', verbose_name='收藏夹'),
        ),
        migrations.AddConstraint(
            model_name='userrelations',
            constraint=models.UniqueConstraint(fields=('following', 'follower'), name='user_relations_uni_sub_follow'),
        ),
        migrations.AddConstraint(
            model_name='userfavorites',
            constraint=models.UniqueConstraint(fields=('user', 'name'), name='user_favarites_uni_user_name'),
        ),
    ]
