from typing import Callable, Optional, Type, Any
from datetime import datetime, timedelta
from django.db import models
from django.core.cache import caches
from django.db.models import Model


class cached_model_property:
    """将model上的方法作为属性，并缓存
    默认缓存库名：default
    默认缓存键格式：model的类名(小写):缓存的方法名:model实例的pk
    note: 更新该属性时仅更新缓存
    使用方式1：无法设置自定义
        @cached_model_property
        def yourself_func(self):
            pass
    使用方式2：
        @cached_model_property(cache=None,timeout=None,expires=None,at=None,version=None)
        def yourself_func(self):
            pass

    使用方式3:
        def yourself_func(self):
            pass
        prop_name = cached_model_property(yourself_func,cache=None,timeout=None,expires=None,at=None,version=None)
    """

    default_cache_name = "default"
    name = None

    def __init__(
        self,
        func: Optional[Callable] = None,
        *,
        cache: Optional[str] = None,
        timeout: Optional[int] = None,
        expires: Optional[dict] = None,
        at: Optional[str] = None,
        version: Optional[int] = None,
    ) -> None:
        self._func = func
        self._cache_name = cache or self.default_cache_name
        self._timeout = timeout
        self._expires = expires
        self._at = at
        self._version = version

    @property
    def timeout(self):
        timeout = None
        if self._expires:
            delta = timedelta(**self._expires)
            timeout = delta.seconds
            if self._at:
                timeout = (
                    datetime.strptime(
                        (datetime.now() + delta).strftime("%Y-%m-%d") + " " + self._at,
                        "%Y-%m-%d %H:%M:%S"
                    )
                    - datetime.now()
                ).seconds
        if self._timeout:
            timeout = self._timeout
        return timeout

    def __call__(self, func: Callable) -> "cached_model_property":
        self._func = func
        return self

    def __set_name__(self, instance: Model, name: str):
        if not hasattr(instance, name):
            self.name = name
        else:
            raise AttributeError(f"无法添加属性{name}: {instance}已有属性: {name}.")

    def __get__(self, instance: Model, cls: Optional[Type[Model]]):
        if not self._func:
            return self
        cache = caches[self._cache_name]
        key = self.get_key(instance)
        res = cache.get(key=key)
        if not res:
            res = self._func(instance)
            cache.set(
                key=key, value=res, timeout=self.timeout, version=self._version
            )
        return res

    def __set__(self, instance: Model, value: Any):
        cache = caches[self._cache_name]
        key = self.get_key(instance=instance)
        cache.set(key=key, value=value, timeout=self.timeout, version=self._version)  # type: ignore

    def __delete__(self, instance):
        cache = caches[self._cache_name]
        key = self.get_key(instance)
        cache.delete(key)  # type: ignore

    def get_key(self, instance):
        return f"{instance.__class__.__name__.lower()}:{instance.pk}:{self.name}"

class ReviewMixinModel(models.Model):
    feedback_choices = [(0, "基本忘了"), (1, "有些忘了"), (2, "基本记得"), (1, "非常清楚")]
    review_date = models.DateField("复习日期", blank=True, null=True)
    review_stage = models.PositiveSmallIntegerField("复习阶段", default=0)
    last_review_date = models.DateField("最近复习日期", blank=True, null=True)
    last_review_feedback = models.PositiveSmallIntegerField(
        "最近复习反馈", blank=True, null=True, choices=feedback_choices
    )

    class Meta:
        abstract = True
