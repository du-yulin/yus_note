from typing import Any
from datetime import datetime,date,timedelta
from django.db.utils import IntegrityError
from rest_framework import serializers


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop("fields", None)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class NestedCurrentModelSerializer(serializers.Serializer):
    """在Serializer中使用该字段时，使用该Serializer序列化指定字段
    用于一个模型的字段外键指定的是自身的字段
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        if isinstance(self.parent, serializers.ListSerializer) or isinstance(self.parent, serializers.ManyRelatedField):
            self.fields = self.parent.parent.fields # type: ignore
            self.Meta = self.parent.parent.Meta # type: ignore
            self.p_class = self.parent.parent
        else:
            self.fields = self.parent.fields # type: ignore
            self.Meta = self.parent.Meta # type: ignore 
            self.p_class = self.parent
        return self.p_class.to_representation(value) # type: ignore 
 

class DateToNowDaysFields(serializers.Field):
    """距今多少天
    to_internal_value: 天数 -> 距今多少天以前的date对象
    to_representation: date对象 -> 距离今天的天数
    note:天数为正表示曾经
    """
    default_error_messages = {
        'datetime': '期望一个date对象，但给了一个datetime对象。',
        'notint': '期望一个int。',
        'notdate': '期望一个date对象。',
    }
    def to_internal_value(self, data:int):
        try:
            data=int(data)
        except ValueError:
            self.fail('notint')
        return date.today() - timedelta(days=data)

    def to_representation(self, value:date):
        if isinstance(value, datetime):
            self.fail('datetime')
        if not isinstance(value,date):
            self.fail('notdate')
        return (date.today()-value).days
    

class DatetimeToNowSecondsFields(serializers.Field):
    """距今多少秒
    to_internal_value: 秒数 -> 距现在多少天以前的date对象
    to_representation: date对象 -> 距离现在的天数
    note:天数为正表示曾经
    """
    default_error_messages = {
        'date': '期望一个datetime对象，但给了一个date对象。',
        'notint': '期望一个int。',
        'notdatetime': '期望一个datetime对象。',
    }
    def to_internal_value(self, data:int):
        try:
            data=int(data)
        except ValueError:
            self.fail('notint')
        return datetime.now() - timedelta(seconds=data)

    def to_representation(self, value:datetime):
        if isinstance(value, date):
            self.fail('date')
        if not isinstance(value, datetime):
            self.fail('notdate')
        return (datetime.now()-value).days


class integrity_error_to_validation_eror:
    """装饰器
    将被装饰函数抛出的IntegrityError转换为serializers.ValidationError
    """
    default_detail = {'detail': '存在重复值。'}
    def __init__(self, detail=None) -> None:
        self.detail = detail or self.default_detail

    def __call__(self, func) -> Any:
        def inner(instance, *args, **kwargs):
            try:
                res = func(instance, *args, **kwargs)
            except IntegrityError:
                raise serializers.ValidationError(self.detail)
            return res
        return inner


