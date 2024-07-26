from typing import cast
from datetime import date, datetime, timedelta
import calendar

from django.http.request import HttpRequest
from django.contrib.auth import login, authenticate, logout
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.mixins import (
    ListModelMixin,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter

from user.models import (
    User,
    UserRelations,
    UserCollections,
    UserFolders,
    UserFavorites,
)
from user_proxy.serializers import (
    AuthCodeSerializer,
    UserDetailSerializer,
    UserUpdateSerializer,
    UserFollowingListSerializer,
    UserFollowingSerializer,
    UserFollowersListSerializer,
    UserCollectionsListSerializer,
    UserCollectionsCreateSerializer,
    UserCollectionsDetailSerializer,
    UserCollectionsUpdateSerializer,
    UserCollectionsPunchSerializer,
    UserFoldersListSerializer,
    UserFoldersSerializer,
    UserFavoritesSerializer,
)
from note.models import Note, NoteComments
from note.serializers import (
    UserNoteListSerializer,
    UserNoteSerializer,
    UserNotePunchSerializer,
    UserNoteRcycleSerializer,
    UserNoteDetailSerializer,
    UserNoteCommentsSerializer,
)
from utils.review import adjust_and_get_next


class AuthCodeView(APIView):
    throttle_scope = "authcode"

    def post(self, request: Request) -> Response:
        """通过手机或者邮箱获取验证码
        -请求参数为'phone'则发送手机验证码
        -请求参数为'email'则发送邮箱验证码

        Returns:
            Response: data格式为请求参数
        """
        serializer = AuthCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """用户手机或邮箱登录,验证码注册登录
    登录方式-请求参数对照表：
        手机号密码登录-phone/password
        邮箱密码登录-email/password
        手机号验证码登录-phone/authcode
        邮箱验证码登录-email/authcode

    """

    def post(self, request: Request) -> Response:
        user = authenticate(
            request, **cast(dict, request.data) # type: ignore
        )  # 验证码登录时，未注册会自动注册
        if not user:
            raise AuthenticationFailed("登录失败！")
        login(cast(HttpRequest, request), user)
        # # 先刷新一下用户复习表
        # refresh_schedule(user)
        serializer = UserDetailSerializer(
            instance=user,
            fields=("id", "username", "nickname", "avator"),
            context={"request": request},
        )
        return Response(serializer.data)


class LogoutView(APIView):
    """用户登出"""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        logout(request=request._request)
        return Response()


# region 需要登录api
class UserView(APIView):
    """
    个人详情、更新
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        """详情"""
        # 每次请求个人信息，先刷新一下个人复习表
        # refresh_schedule(request.user)
        serializer = UserDetailSerializer(
            instance=request.user,
            context={"request": request},
        )
        return Response(serializer.data)

    def post(self, request: Request, *args, **kwargs) -> Response:
        user = request.user
        partial = kwargs.pop("partial", True)

        serializer = UserUpdateSerializer(
            user,
            request.data,
            partial=partial,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        if getattr(user, "_prefetched_objects_cache", None):
            # 如果'prefetch_related'应用到 'queryset'，则需要强行清空缓存
            user._prefetched_objects_cache = {}

        return Response(serializer.data)


class UserFollowingViewSet(
    ListModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    """用户关注：列表、创建、更新、删除"""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return UserFollowingListSerializer
        return UserFollowingSerializer

    def get_queryset(self):
        base_qs = UserRelations.objects.filter(follower=self.request.user)
        if self.action == "list":
            return base_qs.select_related("following")
        return base_qs

    def perform_create(self, serializer):
        serializer.save(follower=self.request.user)

    def perform_update(self, serializer):
        serializer.save(follower=self.request.user)


class UserFollowersViewSet(ListModelMixin, GenericViewSet):
    """用户粉丝：列表"""

    permission_classes = [IsAuthenticated]
    serializer_class = UserFollowersListSerializer

    def get_queryset(self):
        return UserRelations.objects.filter(following=self.request.user).select_related(
            "follower"
        )


def update_history(history: dict):
    """更新历史记录当天+1，删除过期记录"""
    # 如果本月未创建则创建当月记录，并初始化
    now = datetime.now()
    month_str = now.strftime("%Y-%m")
    month_days = calendar.monthrange(now.year, now.month)[1]
    if month_str not in history:
        month_record_list = ["0"] * month_days
        month_record_list[now.day - 1] = "1"
        history[month_str] = ",".join(month_record_list)
    # 如果本月有记录则修改
    else:
        month_record_list = history[month_str].split(",")
        month_record_list[now.day - 1] = str(int(month_record_list[now.day - 1]) + 1)
        history[month_str] = ",".join(month_record_list)
    # 删除过期历史
    history_expires = getattr(settings, "HISTORY_EXPIRES", None) or 90
    expires_dt = now - timedelta(history_expires)
    for k in history:
        if datetime.strptime(k, "%Y-%m") < expires_dt:
            del history[k]
    return history


class UserCollectionsViewSet(ModelViewSet):
    """个人收藏：列表、创建、详情、更新、删除"""

    permission_classes = [IsAuthenticated]
    filter_backends = [OrderingFilter]
    ordering_fields = ["create_time", "last_review_date"]
    ordering = ["-create_time"]

    def get_serializer_class(self):
        if self.action == "list":
            return UserCollectionsListSerializer
        if self.action == "create":
            return UserCollectionsCreateSerializer
        if self.action == "retrieve":
            return UserCollectionsDetailSerializer
        return UserCollectionsUpdateSerializer

    def get_queryset(self):
        base_qs = UserCollections.objects.filter(user=self.request.user)
        if self.action == "list":
            return base_qs.select_related("note")
        return base_qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        note_id = serializer.data["note"]
        note = Note.objects.get(pk=note_id)
        note.likes += 1
        note.save()

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    @action(methods=["POST", "PUT", "PATCH"], detail=True)
    def punch(self, request, pk=None):
        """复习打卡"""
        user = request.user
        collection = get_object_or_404(
            UserCollections.objects.filter(user=user), **{"pk": pk}
        )
        # 调整复习计划、修改历史记录 和 修改笔记复习相关数据
        feed_back = request.data.get("feedback", None)  # type: ignore
        reset = request.data.get("reset", None)  # type: ignore
        new_plan, new_stage, next_review_date = adjust_and_get_next(
            user.review_plan, feed_back, collection.last_review_feedback, collection.review_stage  # type: ignore
        )
        user.review_plan = new_plan  # type: ignore
        update_history(user.review_history)
        user.save()
        collection.review_stage = new_stage if not reset else 0
        collection.review_date = next_review_date
        collection.last_review_date = date.today()
        collection.last_review_feedback = feed_back
        collection.save()
        return Response(UserCollectionsPunchSerializer(collection).data)


class UserFoldersViewSet(
    ListModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    """个人文件夹：列表、创建、更新、删除"""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        base_qs = UserFolders.objects.filter(user=self.request.user)
        if self.action == "list":
            return base_qs.filter(parent=None)
        return base_qs

    def get_serializer_class(self):
        if self.action == "list":
            return UserFoldersListSerializer
        return UserFoldersSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class UserFavoritesViewSet(
    ListModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    serializer_class = UserFavoritesSerializer

    def get_queryset(self):
        return UserFavorites.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class UserNotesViewSet(ModelViewSet):
    """个人笔记：列表、创建、详情、更新、删除"""

    permission_classes = [IsAuthenticated]
    filter_backends = [OrderingFilter]
    ordering_fields = [
        "create_time",
        "update_time",
        "last_review_date",
        "last_review_feedback",
        "views",
        "likes",
    ]
    ordering = ["-create_time"]

    def get_serializer_class(self):
        if self.action == "list":
            return UserNoteListSerializer
        elif self.action == "retrieve":
            return UserNoteDetailSerializer
        return UserNoteSerializer

    def get_queryset(self):
        return Note.objects.filter(author=self.request.user, is_delete=False)

    def perform_create(self, serializer):
        # 创建笔记时更新发布记录
        user = self.request.user
        update_history(user.publish_history)  # type: ignore
        user.save()
        serializer.save(author=user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        permanet = request.data.get("permanet", False)
        if permanet:
            # 删除后删除空标签
            tags = [instance.tags.all()]
            self.perform_destroy(instance)
            for tag in tags:
                if tag.notes.count() == 0:
                    tag.delete()
        else:
            instance.is_delete = True
            instance.delete_date = date.today()
            instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=["POST", "PUT", "PATCH"], detail=True)
    def punch(self, request, pk=None):
        """复习打卡"""
        user = request.user
        note = get_object_or_404(Note.objects.filter(author=user), **{"pk": pk})
        # 调整复习计划、修改复习记录 和 修改笔记复习相关数据
        feed_back = request.data.get("feedback", None)  # type: ignore
        reset = request.data.get("reset", False)  # type: ignore
        new_plan, new_stage, next_review_date = adjust_and_get_next(
            user.review_plan, feed_back, note.last_review_feedback, note.review_stage  # type: ignore
        )
        user.review_plan = new_plan  # type: ignore
        user.review_history = update_history(user.review_history)
        user.save()
        note.review_stage = new_stage if not reset else 0
        note.review_date = next_review_date
        note.last_review_date = date.today()
        note.last_review_feedback = feed_back
        note.save()
        return Response(UserNotePunchSerializer(note).data)

    @action(methods=["GET"], detail=False)
    def rubbish(self, request):
        rubbish_notes = Note.objects.filter(
            author=self.request.user, is_delete=True
        ).order_by("-delete_date")
        serializer = UserNoteListSerializer(rubbish_notes, many=True)
        return Response(serializer.data)

    @action(methods=["POST", "PUT", "PATCH"], detail=True)
    def recycle(self, request, pk=None):
        user = request.user
        note = get_object_or_404(Note.objects.filter(author=user), **{"pk": pk})
        note.is_delete = False
        note.delete_date = None
        note.save()
        serializer = UserNoteRcycleSerializer(note)
        return Response(serializer.data)


class UserCommentsViewSet(CreateModelMixin, DestroyModelMixin, GenericViewSet):
    """用户评论：创建、删除"""

    serializer_class = UserNoteCommentsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NoteComments.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


# endregion
# region 不需要登录api
class TargetUserView(APIView):
    """
    其他用户详情
    """

    def get(self, request: Request, target_user):
        target_user = get_object_or_404(User.objects.all(), id=target_user)
        serializer = UserDetailSerializer(
            instance=target_user,
            context={"request": request},
            fields=(
                "id",
                "username",
                "nickname",
                "email",
                "avator",
                "last_publish_datetime",
                "review_history",
                "publish_history",
                "following_number",
                "followers_number",
            ),
        )
        return Response(serializer.data)


class TargetUserFoldersViewSet(ListModelMixin, GenericViewSet):
    """其他用户文件夹：列表"""

    serializer_class = UserFoldersListSerializer

    def get_queryset(self):
        return UserFolders.objects.filter(
            user=self.kwargs.get("target_user", None), parent=None
        ).prefetch_related("children__children")


class TargetUserFavoritesViewSet(ListModelMixin, GenericViewSet):
    """其他用户收藏夹：列表"""

    serializer_class = UserFavoritesSerializer

    def get_queryset(self):
        return UserFavorites.objects.filter(user=self.kwargs.get("target_user", None))


class TatgetUserCollectionsViewSet(ListModelMixin, GenericViewSet):
    """其他用户收藏：列表"""

    serializer_class = UserCollectionsListSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["create_time"]
    ordering = ["-create_time"]

    def get_queryset(self):
        return UserCollections.objects.filter(
            user=self.kwargs.get("target_user", None)
        ).select_related("note")


class TargetUserNotesViewSet(ListModelMixin, GenericViewSet):
    """用户笔记：列表"""

    filter_backends = [OrderingFilter]
    ordering_fields = ["create_time", "update_time", "views", "likes"]
    ordering = ["-create_time"]

    def get_serializer_class(self):
        return UserNoteListSerializer

    def get_queryset(self):
        return Note.objects.filter(
            author=self.kwargs.get("target_user", None), is_delete=False
        )


# endregion
