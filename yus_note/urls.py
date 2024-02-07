"""
URL configuration for yus_note project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

from apps.user_proxy.views import (
    AuthCodeView,
    ProfessionViewSet,
    LoginView,
    LogoutView,
    UserView,
    UserPTagsViewSet,
    UserFollowingViewSet,
    UserFollowersViewSet,
    UserCollectionsViewSet,
    UserFoldersViewSet,
    UserFavoritesViewSet,
    UserNotesViewSet,
    TargetUserView,
    TargetUserFoldersViewSet,
    TargetUserFavoritesViewSet,
    TatgetUserCollectionsViewSet,
    TargetUserNotesViewSet,
    UserCommentsViewSet,
)
from apps.note.views import (
    NoteTagViewSet,
    NoteViewSet,
    NoteCommentsViewSet,
    NoteTagSearchViewSet,
    NoteSearchViewSet,
)


router = DefaultRouter()
router.register("professions", ProfessionViewSet, "professions")
router.register("user/tags", UserPTagsViewSet, "user_tags")
router.register("user/following", UserFollowingViewSet, "user_following")
router.register("user/followers", UserFollowersViewSet, "user_followers")
router.register("user/collections", UserCollectionsViewSet, "user_collections")
router.register("user/folders", UserFoldersViewSet, "user_folders")
router.register("user/favorites", UserFavoritesViewSet, "user_favorites")
router.register("user/notes", UserNotesViewSet, "user_notes")
router.register("notetags", NoteTagViewSet, "notetags")
router.register("notes", NoteViewSet, "notes")
router.register("user/comments", UserCommentsViewSet, "user_comments")
router.register("search/notetags", NoteTagSearchViewSet, "notetags_search")
router.register("search/notes", NoteSearchViewSet, "notes_search")

taget_user_router = DefaultRouter()  # 定义路径user/id/...格式的路由
taget_user_router.register("folders", TargetUserFoldersViewSet, "target_user_folders")
taget_user_router.register(
    "favorites", TargetUserFavoritesViewSet, "target_user_favorites"
)
taget_user_router.register(
    "collections", TatgetUserCollectionsViewSet, "target_user_collections"
)
taget_user_router.register("notes", TargetUserNotesViewSet, "target_user_notes")

target_note_router = DefaultRouter()
target_note_router.register("comments", NoteCommentsViewSet, "target_note_comments")

urlpatterns = [
    path("admin/", admin.site.urls, name="admin"),
    path("api-auth/", include("rest_framework.urls"), name="api_auth"),
    path("social-auth/", include("social_django.urls"), name="social_auth"),
    path("tinymce/", include("tinymce.urls"), name="tinymce"),
    path("authcode/", AuthCodeView.as_view(), name="authcode"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("user/profile/", UserView.as_view(), name="user_profile"),
    path(
        "user/<int:target_user>/profile/",
        TargetUserView.as_view(),
        name="target_user_profile",
    ),
]
urlpatterns += router.urls
urlpatterns += [  # 由于router的url不能使用django的url转换器，因此需要将其包裹在一个include path中
    path("user/<int:target_user>/", include(taget_user_router.urls)),
    path("notes/<int:target_note>/", include(target_note_router.urls)),
]
# 文件服务
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
