from typing import Union, Any, Type, Optional

from django.conf import settings
from django.db import models
from django.apps import apps
from django.contrib import auth
from django.contrib.auth.hashers import make_password
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, Permission
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.mail import send_mail
from django.utils.deconstruct import deconstructible

from tinymce.models import HTMLField

from yus_note.models import ReviewMixinModel, cached_model_property
from user.validators import FileSizeValidator


def user_avator_upload_path(instance: "User", filename: str) -> str:
    filename_ext = filename.rsplit(".", 1)[1]
    return f"user/avators/{instance.pk}-{instance.username}.{filename_ext}"


class UserManager(BaseUserManager):
    """
    用户管理类
    """

    use_in_migrations = True

    def _create_user(
        self, username: str, password: Optional[str], **extra_fields
    ) -> "User":
        if not username:
            raise ValueError("必须提供用户名")

        if "email" in extra_fields:
            extra_fields["email"] = self.normalize_email(extra_fields["email"])
        user_model: Type[AbstractBaseUser] = apps.get_model(
            self.model._meta.app_label, self.model._meta.object_name
        )  # type: ignore
        username = user_model.normalize_username(username)
        user = self.model(username=username, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self, username: str, password: Optional[str] = None, **extra_fields
    ) -> "User":
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, password, **extra_fields)

    def create_superuser(
        self, username: str, password: Optional[str] = None, **extra_fields
    ) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(username, password, **extra_fields)

    def with_perm(
        self,
        perm: Union[str, Permission],
        is_active: bool = True,
        include_superusers: bool = True,
        backend: Optional[str] = None,
        obj: Optional["User"] = None,
    ) -> Any:
        if backend is None:
            backends = auth.get_backends()
            if len(backends) == 1:
                rel_backend = backends[0]
            else:
                raise ValueError(
                    "You have multiple authentication backends configured and "
                    "therefore must provide the `backend` argument."
                )
        elif not isinstance(backend, str):
            raise TypeError(
                "backend must be a dotted import path string (got %r)." % backend
            )
        else:
            rel_backend = auth.load_backend(backend)
        if hasattr(rel_backend, "with_perm"):
            return rel_backend.with_perm(
                perm,
                is_active=is_active,
                include_superusers=include_superusers,
                obj=obj,
            )
        return self.none()


def default_history():
    return {}


class User(AbstractBaseUser, PermissionsMixin):
    """
    用户模型
    """

    avator_validator = FileSizeValidator(max_size="2MB")

    username = models.CharField(
        "用户名",
        max_length=64,
        help_text="必填。50个以内的字符、数字、或者特殊字符(@ . + - _)。",
        validators=[UnicodeUsernameValidator()],
        error_messages={"unique": "该用户名已经存在！"},
    )

    nickname = models.CharField(
        "昵称",
        max_length=8,
        blank=True,
        help_text="8个以内字符。",
    )

    phone = models.CharField(
        "手机号",
        max_length=11,
        null=True,
        blank=True,
        error_messages={"unique": "该手机号已注册！"},
    )

    email = models.EmailField(
        "邮箱", blank=True, null=True, error_messages={"unique": "该邮箱已注册！"}
    )

    avator = models.ImageField(
        "头像",
        upload_to=user_avator_upload_path,  # type: ignore
        blank=True,
        null=True,
        validators=[avator_validator],
    )

    resume = HTMLField("简介", default="", max_length=256, help_text="个人简介")

    is_staff = models.BooleanField(
        "是否为管理员", default=False, help_text="是否可以登录后台管理系统。"
    )

    is_active = models.BooleanField("是否激活", default=True)

    registration_date = models.DateField("注册日期", auto_now_add=True)

    last_publish_datetime = models.DateTimeField(
        "最近发布时间", null=True, blank=True, help_text="最近发布笔记时间。"
    )

    review_history = models.JSONField(
        "复习记录",
        default=default_history,
        blank=True,
        help_text="笔记复习记录: 键为日期字符串; 值为每天复习数量, 每天复习数量使用','隔开。",
    )

    publish_history = models.JSONField(
        "发布记录",
        default=default_history,
        blank=True,
        help_text="笔记发布记录: 键为日期字符串; 值为每天复习数量, 每天复习数量使用','隔开。",
    )

    review_plan = models.CharField(
        "复习计划",
        max_length=64,
        default=settings.DEFAULT_REVIEW_PLAN,
        help_text="分别在多少天后复习笔记，使用','连接多个天数（如：'1,3,7,30'表示新的笔记分别在1、3、7天后进行复习）。",
    )

    following = models.ManyToManyField(
        verbose_name="关注",
        to="self",
        symmetrical=False,
        blank=True,
        related_name="followers",
        through="UserRelations",
        through_fields=("following", "follower"),
    )

    collected_notes = models.ManyToManyField(
        verbose_name="收藏的笔记",
        to="note.Note",
        related_name="collectors",
        blank=True,
        through="UserCollections",
        through_fields=("user", "note"),
    )

    objects = UserManager()
    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    PHONE_FIELD = "phone"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(fields=["username"], name="user_uni_username"),
            models.UniqueConstraint(fields=["phone"], name="user_uni_phone"),
            models.UniqueConstraint(fields=["email"], name="user_uni_email"),
        ]

    def clean(self) -> None:
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)  # type: ignore

    def email_user(
        self, subject: str, message: str, from_email: Union[str, None] = None, **kwargs
    ) -> None:
        """Send an email to this user."""
        if self.email:
            send_mail(subject, message, from_email, [self.email], **kwargs)

    @cached_model_property(cache="model_fields")
    def following_number(self) -> int:
        return self.rel_following.count()  # type: ignore

    @cached_model_property(cache="model_fields")
    def followers_number(self) -> int:
        return self.rel_followers.count()  # type: ignore

    @property
    def name(self):
        return self.nickname or self.username

    def __str__(self) -> str:
        return "{}:{}".format(self.username, self.nickname or "--")


class UserRelations(models.Model):
    """用户关系"""

    following = models.ForeignKey(
        verbose_name="被关注用户",
        to=User,
        related_name="rel_followers",
        on_delete=models.CASCADE,
        limit_choices_to={"is_active": True},
    )
    follower = models.ForeignKey(
        verbose_name="用户",
        to=User,
        related_name="rel_following",
        on_delete=models.CASCADE,
        limit_choices_to={"is_active": True},
    )

    class Meta:
        verbose_name = "用户关系"
        verbose_name_plural = "用户关系"
        db_table = "user_user_relations"
        constraints = [
            models.UniqueConstraint(
                fields=["following", "follower"], name="user_relations_uni_sub_follow"
            )
        ]


class UserFolders(models.Model):
    """用户文件夹"""

    name = models.CharField("名称", max_length=32)
    parent = models.ForeignKey(
        verbose_name="父级文件夹",
        to="self",
        on_delete=models.SET_NULL,
        related_name="children",
        blank=True,
        null=True,
    )
    user = models.ForeignKey(
        verbose_name="用户",
        to=User,
        on_delete=models.CASCADE,
        related_name="folders",
        limit_choices_to={"is_active": True},
    )

    class Meta:
        verbose_name = "用户文件夹"
        verbose_name_plural = verbose_name
        db_table = "user_user_folders"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "parent"], name="user_folders_uni_name_parent"
            )
        ]

    def __str__(self) -> str:
        return "{}/{}".format(self.parent, self.name)


class UserFavorites(models.Model):
    name = models.CharField("名称", max_length=32)
    user = models.ForeignKey(
        verbose_name="用户",
        to=User,
        on_delete=models.CASCADE,
        related_name="favorites",
        limit_choices_to={"is_active": True},
    )
    notes = models.ManyToManyField(
        verbose_name="收藏笔记",
        to="note.Note",
        related_name="favorites",
        through="UserCollections",
        through_fields=("favorite", "note"),
        blank=True,
    )

    class Meta:
        verbose_name = "用户收藏夹"
        verbose_name_plural = verbose_name
        db_table = "user_user_favarites"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"], name="user_favarites_uni_user_name"
            )
        ]

    def __str__(self) -> str:
        return "{}".format(self.name)


class UserCollections(ReviewMixinModel, models.Model):
    """
    用户收藏
    """

    user = models.ForeignKey(
        verbose_name="用户",
        to=User,
        on_delete=models.CASCADE,
        related_name="collections",
        limit_choices_to={"is_active": True},
    )
    note = models.ForeignKey(
        verbose_name="笔记",
        to="note.Note",
        on_delete=models.CASCADE,
        related_name="collections",
        limit_choices_to={"is_delete": False},
    )
    favorite = models.ForeignKey(
        verbose_name="收藏夹",
        to=UserFavorites,
        related_name="collections",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    create_time = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "用户收藏"
        verbose_name_plural = verbose_name
        db_table = "user_user_collections"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "note"], name="user_collections_uni_user_note"
            )
        ]

    def __str__(self) -> str:
        return "{}/{}".format(self.favorite, self.note.name)
