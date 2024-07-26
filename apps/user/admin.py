from django.contrib import admin

from user.models import User, UserFolders, UserCollections
# Register your models here.


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(UserFolders)
class UserFoldersAdmin(admin.ModelAdmin):
    pass


@admin.register(UserCollections)
class UserCollectionsAdmin(admin.ModelAdmin):
    pass




