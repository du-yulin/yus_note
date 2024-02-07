from typing import Union
import re

from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class PhoneValidator(RegexValidator):
    regex = r"^((13[0-9])|(14[5,7])|(15[0-3,5-9])|(17[0,3,5-8])|(18[0-9])|166|198|199|(147))\d{8}$"
    message = "请填写11位的手机号。"


@deconstructible
class FileSizeValidator:
    unit_muti_map = {
        "KB": 1 << 10,
        "MB": 1 << 20,
    }

    def __init__(self, max_size: Union[str, int, float]) -> None:
        """FileField的文件大小验证

        Args:
            max_size (Union[str,int]): 为int时表示文件字节数，为str时仅支持KB/MB写法
            min_size (Union[str,int], optional): 为int时表示文件字节数，为str时仅支持KB/MB写法
        """
        self.raw_max_size = max_size
        self.max_size = (
            max_size if isinstance(max_size, (int, float)) else self._get_size(max_size)
        )

    def _get_size(self, size: str) -> float:
        pattern = rf"([\d.]+)({''.join([i+'|' for i in self.unit_muti_map])[:-1]})"
        res = re.match(pattern=pattern, string=size.upper().strip())
        if res:
            groups = res.groups()
            return float(groups[0]) * self.unit_muti_map[groups[1]]
        return 0

    def __call__(self, file):
        if not file:
            raise ValidationError("文件为None。")
        if file.size > self.max_size:
            raise ValidationError(f"文件太大, 请上传一个{self.raw_max_size}以内的文件。")
