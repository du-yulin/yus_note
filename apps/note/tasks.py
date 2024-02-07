from celery import shared_task
from redis import Redis, ConnectionPool
from django.conf import settings
from django.utils.log import DEFAULT_LOGGING
from note.models import Note

@shared_task
def synchronize_note_views():
    pool = ConnectionPool.from_url(settings['CACHES']['model_fields']['LOCATION'])
    redis = Redis(connection_pool=ConnectionPool)
    keys = redis.keys('note:cached_views:*')
    keys = [k.decode() for k in keys] # type: ignore
    views_list = redis.mget(keys) # type: ignore
    id_list = [int(k.split(':')[-1]) for k in keys]
    views_list = [int(k.decode()) for k in views_list] # type: ignore
    for k,v in zip(id_list,views_list): # type: ignore
        try:
            note = Note.objects.get(pk=k)
        except Note.DoesNotExist:
            continue
        else:
            note.views = v
            note.save()


    
