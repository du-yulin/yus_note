"""公共drf权限"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user==request.user # type:ignore
    

class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.user==request.user # type:ignore
    

class IsAuthor(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author==request.user # type:ignore
    

class IsAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.author==request.user # type:ignore
    

