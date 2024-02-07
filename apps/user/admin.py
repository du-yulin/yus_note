from django.contrib import admin

from user.models import Profession, User, UserProfessionTags, UserFolders, UserCollections
# Register your models here.
@admin.register(Profession)
class ProfessionAdmin(admin.ModelAdmin):
    pass


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(UserProfessionTags)
class UserProfessionTagsAdmin(admin.ModelAdmin):
    pass


@admin.register(UserFolders)
class UserFoldersAdmin(admin.ModelAdmin):
    pass


@admin.register(UserCollections)
class UserCollectionsAdmin(admin.ModelAdmin):
    pass




