import random
from datetime import date

from django.conf import settings
from django.core.cache import caches
from django.core.validators import EmailValidator
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from yus_note.drf.serializers import (
    DynamicFieldsModelSerializer,
    NestedCurrentModelSerializer,
    DateToNowDaysFields,
)
from user.models import (
    Profession,
    User,
    UserProfessionTags,
    UserRelations,
    UserCollections,
    UserFolders,
    UserFavorites,
)
from user.validators import PhoneValidator
from note.serializers import UserNoteListSerializer, NoteDetailSerializer


class AvatorField(serializers.ImageField):
    def to_representation(self, value):
        if not value:
            url = str(getattr(settings, "DEFAULT_AVATOR", None))
            request = self.context.get("request", None)
            if request is not None:
                return request.build_absolute_uri(url)
            return url

        return super().to_representation(value=value)


class AuthCodeSerializer(serializers.Serializer):
    """验证码序列化"""

    email = serializers.CharField(
        required=False, validators=[EmailValidator()], label="邮箱"
    )
    phone = serializers.CharField(
        required=False, validators=[PhoneValidator()], label="手机号"
    )

    def validate(self, data: dict):
        email = data.get("email", None)
        phone = data.get("phone", None)
        if not email and not phone:
            raise serializers.ValidationError(
                {"email": ["手机号不能为空！"], "phone": ["邮箱不能为空！"]}
            )
        return data

    def create(self, validated_data: dict):
        phone = validated_data.get("phone", None)
        email = validated_data.get("email", None)
        code = str(random.randint(0, 999999)).zfill(6)
        if phone:
            to = phone
            pass
            # res = SMS('authcode').send_sms(to_list=[phone], param_list=[code])
            # if not res["successes"]:
            #     raise ServerError(res["message"])
        else:
            to = email
            # res = send_mail(
            #     subject=settings.AUTHCODE_EMAIL_SUBJECT_TEMPLATE,
            #     message="",
            #     from_email=settings.EMAIL_HOST_USER,
            #     recipient_list=[email],
            #     html_message=settings.AUTHCODE_EMAIL_CONTENT_TEMPLATE.format(code),
            # )
            # if not res:
            #     raise ServerError("邮件发送失败")
        cache_name = getattr(settings, "DEFAULT_AUTHCODE_CACHE", "default")
        caches[cache_name].set(f"authcode:{to}", code)
        print(f"\033[1;36;40m[authcode] {code} ====> {to}\033[0m")
        return validated_data


class ProfessionSerializer(DynamicFieldsModelSerializer):
    """行业序列化"""

    children = NestedCurrentModelSerializer(many=True)

    class Meta:
        model = Profession
        fields = ["id", "name", "children"]


class UserListSerializer(serializers.ModelSerializer):
    """用户：列表"""

    name = serializers.CharField()
    avator = AvatorField()

    class Meta:
        model = User
        fields = ("id", "name", "avator")


class UserDetailSerializer(DynamicFieldsModelSerializer):
    """用户序列化：详情"""

    # profession_tags = UserPTagsListSerializer(many=True)
    following_number = serializers.IntegerField()
    followers_number = serializers.IntegerField()
    avator = AvatorField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "nickname",
            "email",
            "phone",
            "avator",
            "gender",
            "registration_date",
            "last_publish_datetime",
            "review_history",
            "publish_history",
            "following_number",
            "followers_number",
        )


class UserUpdateSerializer(serializers.ModelSerializer):
    """用户序列化：更新"""

    class Meta:
        model = User
        fields = (
            "nickname",
            "email",
            "phone",
            "avator",
            "gender",
            "password",
        )

    def validate_password(self, value: str) -> str:
        user = self.instance
        validate_password(password=value, user=user)
        return value

    def validate(self, data):
        """
        Args:
            data: 若更新密码，则request需要authcode(验证码)、password_repeat(重复密码)与authcode_way(发送验证码方式:email/phone)
        """
        user = self.instance
        password = data.get("password", None)
        if self.initial_data is not serializers.empty and password:
            authcode = self.initial_data.pop("authcode", None)  # type: ignore
            authcode_way = self.initial_data.pop("authcode_way", None)  # type: ignore
            password_repeat = self.initial_data.pop("password_repeat", None)  # type: ignore

            self.__validate_password_repeat(password_repeat, password)
            self.__validate_authcode(authcode, authcode_way, user)  # type: ignore

        return data

    def __validate_authcode(self, authcode: str, authcode_way: str, user: User):
        if not authcode_way or authcode_way not in ("email", "phone"):
            raise serializers.ValidationError({"authcode_way": ["请选择验证码发送方式！"]})

        cache_name = getattr(settings, "DEFAULT_AUTHCODE_CACHE", "default")
        # 手机与邮箱都会检测
        real_authcode = (
            caches[cache_name].get(f"authcode:{user.phone}")
            if authcode_way == "phone"
            else caches[cache_name].get(f"authcode:{user.email}")
        )
        if real_authcode != authcode:
            raise serializers.ValidationError({"authcode": ["验证码错误！"]})

    def __validate_password_repeat(self, password_repeat: str, password: str):
        if password != password_repeat:
            raise serializers.ValidationError({"password_repeat": ["两次密码不一致！"]})

    def update(self, instance: User, validated_data: dict):
        # 如果需要更改密码，则先更新密码，再更新其他普通信息
        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)

        return super().update(instance, validated_data)


class UserPTagsListSerializer(serializers.ModelSerializer):
    """用户行业标签序列化：列表"""

    profession = ProfessionSerializer(fields=["id", "name"])
    experience = DateToNowDaysFields(source="entry_date")

    class Meta:
        model = UserProfessionTags
        fields = ["id", "profession", "experience"]


class UserPTagsSerializer(serializers.ModelSerializer):
    """用户行业标签序列化：创建、更新"""

    experience = DateToNowDaysFields(source="entry_date")

    class Meta:
        model = UserProfessionTags
        fields = ["id", "profession", "experience"]

    def validate_experience(self, value):
        if value > date.today():
            raise serializers.ValidationError("经验不能为负数。")
        return value

    def validate_profession(self, value):
        user = self.context["request"].user
        if UserProfessionTags.objects.filter(user=user, profession=value).exists():
            raise serializers.ValidationError("已有该职业标签。")
        return value


class UserFollowingListSerializer(serializers.ModelSerializer):
    """用户关注：列表"""

    following = UserListSerializer()

    class Meta:
        model = UserRelations
        fields = ("id", "following")


class UserFollowingSerializer(serializers.ModelSerializer):
    """用户关注：创建、更新、删除"""

    class Meta:
        model = UserRelations
        fields = ("id", "following")

    def validate_following(self, value):
        user = self.context["request"].user
        if value == user:
            raise serializers.ValidationError("不能关注自己！")
        if UserRelations.objects.filter(follower=user, following=value).exists():
            raise serializers.ValidationError("已经关注了该用户！")
        return value


class UserFollowersListSerializer(serializers.ModelSerializer):
    """用户粉丝：列表"""

    follower = UserListSerializer()

    class Meta:
        model = UserRelations
        fields = ("id", "follower")


class UserCollectionsListSerializer(serializers.ModelSerializer):
    """用户收藏项序列化：列表"""

    note = UserNoteListSerializer()

    class Meta:
        model = UserCollections
        fields = ("id", "note")


class UserCollectionsCreateSerializer(serializers.ModelSerializer):
    """用户收藏项序列化：创建"""

    class Meta:
        model = UserCollections
        fields = ("id", "note", "favorite")

    def validate_favorite(self, value):
        user = self.context["request"].user
        # 没有指定文件夹则指定根文件夹
        if value and value.user != user:
            raise serializers.ValidationError("非法的收藏夹！")
        return value

    def validate_note(self, value):
        user = self.context["request"].user
        if value.author == user:
            raise serializers.ValidationError("不能收藏自己的笔记！")
        if UserCollections.objects.filter(user=user, note=value).exists():
            raise serializers.ValidationError("已经收藏过该笔记！")
        return value


class UserCollectionsUpdateSerializer(UserCollectionsCreateSerializer):
    """用户收藏项序列化：更新"""

    class Meta:
        model = UserCollections
        fields = ["id", "favorite"]


class UserCollectionsPunchSerializer(serializers.ModelSerializer):
    """用户收藏项：更新（打卡）"""

    class Meta:
        model = UserCollections
        fields = ["id", "last_review_date", "last_review_feedback"]


class UserCollectionsDetailSerializer(serializers.ModelSerializer):
    """用户收藏项：详情"""

    note = NoteDetailSerializer()

    class Meta:
        model = UserCollections
        fields = ["id", "note", "last_review_date", "last_review_feedback"]
        read_only_fields = ["last_review_date", "last_review_feedback"]


class UserFoldersListSerializer(serializers.ModelSerializer):
    """用户文件夹序列化：列表"""

    children = NestedCurrentModelSerializer(many=True)

    class Meta:
        model = UserFolders
        fields = ("id", "name", "children")


class UserFoldersSerializer(serializers.ModelSerializer):
    """用户文件夹序列化：创建、更新"""

    class Meta:
        model = UserFolders
        fields = ("id", "name", "parent")

    def validate_parent(self, value):
        req = self.context["request"]
        if value and not value.user == req.user:
            raise serializers.ValidationError("不能移动到非本人文件夹。")
        return value

    def validate(self, data):
        user = self.context["request"].user
        if UserFolders.objects.filter(
            user=user, name=data["name"], parent=data["parent"]
        ).exists():
            raise serializers.ValidationError({"name": ["该目录下已有同名文件夹。"]})
        return data


class UserFavoritesSerializer(serializers.ModelSerializer):
    """用户收藏夹：列表、创建、更新、删除"""

    class Meta:
        model = UserFavorites
        fields = ("id", "name")

    def validate_name(self, value):
        # 如果已有则抛错
        user = self.context["request"].user
        if UserFavorites.objects.filter(user=user, name=value).exists():
            raise serializers.ValidationError("已有该名字收藏夹！")
        return value
