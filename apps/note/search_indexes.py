from haystack import indexes
from note.models import Tag, Note


class NoteTagIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    # id = indexes.CharField(model_attr='pk')
    # name = indexes.CharField(model_attr='name')
    
    def get_model(self):
        return Tag

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
    

class NoteIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    # id = indexes.CharField(model_attr='pk')
    # title = indexes.CharField(model_attr='title')
    # views = indexes.IntegerField(model_attr='views')
    # likes = indexes.IntegerField(model_attr='likes')

    def get_model(self):
        return Note
    
    def index_queryset(self, using=None):
        return self.get_model().objects.filter(is_delete=False)


