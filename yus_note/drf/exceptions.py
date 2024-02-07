"""公共drf异常
"""

from rest_framework.exceptions import APIException
from rest_framework import status


class ServerError(APIException):
    """服务器错误异常
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = '服务器错误'
    default_code = 'server error'



