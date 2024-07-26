from django.contrib import admin

from note.models import Tag, Note, NoteComments, Category
# Register your models here.

@admin.register(Category)
class NoteCategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Tag)
class NoteTagAdmin(admin.ModelAdmin):
    pass


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    pass


@admin.register(NoteComments)
class NoteCommentsAdmin(admin.ModelAdmin):
    pass