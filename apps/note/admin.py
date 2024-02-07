from django.contrib import admin

from note.models import NoteTag, Note, NoteComments
# Register your models here.

@admin.register(NoteTag)
class NoteTagAdmin(admin.ModelAdmin):
    pass


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    pass


@admin.register(NoteComments)
class NoteCommentsAdmin(admin.ModelAdmin):
    pass