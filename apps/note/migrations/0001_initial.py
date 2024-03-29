# Generated by Django 4.2.1 on 2024-01-15 21:09

from django.db import migrations, models
import tinymce.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('review_date', models.DateField(blank=True, null=True, verbose_name='复习日期')),
                ('last_review_date', models.DateField(blank=True, null=True, verbose_name='最近复习日期')),
                ('last_review_score', models.FloatField(blank=True, null=True, verbose_name='最近复习熟悉程度')),
                ('title', models.CharField(max_length=32, verbose_name='主题')),
                ('is_private', models.BooleanField(default=False, verbose_name='是否私有')),
                ('content', tinymce.models.HTMLField(verbose_name='内容')),
                ('likes', models.PositiveIntegerField(default=0, verbose_name='点赞数')),
                ('views', models.PositiveIntegerField(default=0, verbose_name='浏览量')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='最近更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='是否已删除')),
            ],
            options={
                'verbose_name': '笔记',
                'verbose_name_plural': '笔记',
            },
        ),
        migrations.CreateModel(
            name='NoteComments',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.CharField(max_length=120, verbose_name='内容')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
            ],
            options={
                'verbose_name': '笔记评论',
                'verbose_name_plural': '笔记评论',
                'db_table': 'note_note_comments',
            },
        ),
        migrations.CreateModel(
            name='NoteTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, unique=True, verbose_name='名称')),
            ],
            options={
                'verbose_name': '笔记标签',
                'verbose_name_plural': '笔记标签',
                'db_table': 'note_tag',
            },
        ),
        migrations.AddConstraint(
            model_name='notetag',
            constraint=models.UniqueConstraint(fields=('name',), name='note_tag_uni_name'),
        ),
    ]
