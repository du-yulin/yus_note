from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, CreateModelMixin
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_haystack.viewsets import HaystackViewSet

from note.models import Note, NoteTag, NoteComments
from note.serializers import (
    NoteListSerializer,
    NoteDetailSerializer,
    NoteTagSerializer,
    NoteCommentsListSerializer,
    NoteTagHaystackSerializer,
    NoteHaystackSerializer,
)


# Create your views here.
class NoteTagViewSet(CreateModelMixin, ListModelMixin, GenericViewSet):
    """笔记标签：列表"""

    queryset = NoteTag.objects.all()
    serializer_class = NoteTagSerializer


class NoteViewSet(ListModelMixin, GenericViewSet):
    """笔记：列表、详情"""

    queryset = Note.objects.filter(is_private=False, is_delete=False).select_related(
        "author"
    )
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["views", "likes", "create_time", "update_time"]
    ordering = ["-views"]

    def get_serializer_class(self):
        if self.action == "list":
            return NoteListSerializer
        return NoteDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            isinstance.views += 1
            instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class NoteCommentsViewSet(ListModelMixin, GenericViewSet):
    """笔记评论：列表"""

    serializer_class = NoteCommentsListSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["create_time"]
    ordering = ["-create_time"]

    def get_queryset(self):
        target_note = self.kwargs.get("target_note", None)
        return NoteComments.objects.filter(note=target_note).select_related("author")


class NoteTagSearchViewSet(HaystackViewSet):
    """笔记标签搜索：列表"""
    index_models = [NoteTag]
    serializer_class = NoteTagHaystackSerializer


class NoteSearchViewSet(HaystackViewSet):
    """笔记搜索：列表"""
    index_models = [Note]
    serializer_class = NoteHaystackSerializer


