from typing import Optional, Type
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.core.cache import caches


UserModel: Type[AbstractBaseUser] = get_user_model()


class FieldPasswordBackend(ModelBackend):
    def auth(
        self,
        field_name: str,
        field_value: Optional[str],
        password: Optional[str],
        **kwargs,
    ):
        """根据字段和密码验证用户

        Args:
            field_name (str): 字段名
            field_value (Optional[str]): 字段值
            password (Optional[str]): 密码

        Returns:
            Optional[UserModel]: 用户实例
        """
        if field_value is None:
            field_value = kwargs.get(field_name)
        if field_value is None or password is None:
            return
        try:
            user = UserModel._default_manager.get(**{field_name: field_value})
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            UserModel().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user

    # def get_user(self, user_id):
    #     """加速用户获取profession属性？"""
    #     try:
    #         user = UserModel._default_manager.get(pk=user_id)
    #     except UserModel.DoesNotExist:
    #         return None
    #     return user if self.user_can_authenticate(user) else None

    def authenticate(self, request: HttpRequest, **kwargs):
        raise NotImplementedError


class FieldAuthcodeBackend(ModelBackend):
    def auth(
        self, field_name: str, field_value: Optional[str], authcode: Optional[str]
    ):
        """根据字段和验证码验证用户

        Args:
            field_name (str): 字段名
            field_value (Optional[str]): 字段值
            authcode (Optional[str]): 验证码

        Returns:
            Optional[UserModel]: 用户实例
        """
        if field_value is None or authcode is None:
            return
        if not self.check_authcode(field_value, authcode):
            return
        user = None
        try:
            user = UserModel._default_manager.get(**{field_name: field_value})
        except UserModel.DoesNotExist:
            # 没有匹配用户则创建用户
            user = UserModel.objects.create_user(  # type: ignore
                username=field_value,
                **{field_name: field_value},
            )
        return user

    def check_authcode(self, field_value: str, authcode: str) -> bool:
        """验证验证码

        Args:
            field_value str: 字段值
            authcode (str): 验证码

        Returns:
            bool: 是否通过验证
        """
        cache_name = getattr(settings, "DEFAULT_AUTHCODE_CACHE", "default")
        real_authcode = caches[cache_name].get(f"authcode:{field_value}")
        return authcode == real_authcode


class EmailPasswordBackend(FieldPasswordBackend):
    """
    邮箱-密码认证
    """

    def authenticate(
        self,
        request: HttpRequest,
        email: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs,
    ):
        return self.auth(UserModel.EMAIL_FIELD, email, password)  # type:ignore


class EmailAuthcodeBackend(FieldAuthcodeBackend):
    """
    邮箱-验证码认证
    """

    def authenticate(
        self,
        request: HttpRequest,
        email: Optional[str] = None,
        authcode: Optional[str] = None,
        **kwargs,
    ):
        return self.auth(UserModel.EMAIL_FIELD, email, authcode)  # type:ignore


class PhonePasswordBackend(FieldPasswordBackend):
    """
    手机-密码认证
    """

    def authenticate(
        self,
        request: HttpRequest,
        phone: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs,
    ):
        return self.auth(UserModel.PHONE_FIELD, phone, password)  # type:ignore


class PhoneAuthcodeBackend(FieldAuthcodeBackend):
    """
    手机-验证码认证
    """

    def authenticate(
        self,
        request: HttpRequest,
        phone: Optional[str] = None,
        authcode: Optional[str] = None,
        **kwargs,
    ):
        return self.auth(UserModel.PHONE_FIELD, phone, authcode)  # type:ignore
