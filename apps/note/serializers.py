from django.db import transaction
from rest_framework import serializers
from drf_haystack import serializers as haystack_serializers

from note.models import Note, Tag, NoteComments
from user.models import User, UserFolders
from note.search_indexes import NoteTagIndex, NoteIndex


class AuthorSerializer(serializers.ModelSerializer):
    name = serializers.CharField()

    class Meta:
        model = User
        fields = ["id", "name"]


class NoteFolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFolders
        fields = ["id", "name"]


class NoteTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class UserNoteListSerializer(serializers.ModelSerializer):
    """用户笔记：列表"""

    tags = NoteTagSerializer(many=True)

    class Meta:
        model = Note
        fields = ("id", "tags", "title", "views", "likes", "is_private")


class NoteListSerializer(serializers.ModelSerializer):
    """笔记：列表（大厅）"""

    class Meta:
        model = Note
        fields = ("id", "title", "views", "likes")


class UserNoteSerializer(serializers.ModelSerializer):
    """个人笔记：创建、更新、删除"""

    tags = NoteTagSerializer(many=True)

    class Meta:
        model = Note
        fields = ("id", "tags", "category", "title", "is_private", "folder", "content")

    def validate_folder(self, value):
        user = self.context["request"].user
        if value and value.user != user:
            raise serializers.ValidationError("非法的文件夹！")
        return value

    def validate(self, data):
        user = self.context["request"].user
        if Note.objects.filter(
            author=user, folder=data["folder"], title=data["title"]
        ).exists():
            raise serializers.ValidationError({"title": ["该标题在该文件夹中已存在！"]})
        return data

    def create(self, validated_data):
        with transaction.atomic():
            tags_data = validated_data.pop("tags")
            tags = [
                Tag.objects.get_or_create(id=t.pop("id", None), defaults=t)[0]
                for t in tags_data
            ]
            note: Note = super().create(validated_data)
            note.tags.set(tags, through_defaults={"category": note.category})
            return note

    def update(self, instance, validated_data):
        with transaction.atomic():
            tags_data = validated_data.pop("tags")
            tags = [
                Tag.objects.get_or_create(id=t.pop("id", None), defaults=t)[0]
                for t in tags_data
            ]
            tags_id = [t.id for t in tags]  # type: ignore

            old_tags = instance.tags.all()
            old_tags_id = [t.id for t in old_tags]  # type: ignore

            note: Note = super().update(instance, validated_data)
            note.tags.set(tags, through_defaults={"category": note.category})
            # 删除空标签
            diff_tags_id = set(old_tags_id) - set(tags_id)
            for id in diff_tags_id:
                tag = Tag.objects.get(id=id)
                if tag.notes.count() <= 1:  # type: ignore
                    tag.delete()
            return note


class UserNotePunchSerializer(serializers.ModelSerializer):
    """个人笔记：打卡返回"""

    class Meta:
        model = Note
        fields = ("id", "last_review_date", "last_review_feedback")


class UserNoteRcycleSerializer(serializers.ModelSerializer):
    """个人笔记：回收返回"""

    class Meta:
        model = Note
        fields = ("id", "is_delete")


class NoteDetailSerializer(serializers.ModelSerializer):
    """笔记：详情"""

    author = AuthorSerializer()
    folder = NoteFolderSerializer()
    tags = NoteTagSerializer()

    class Meta:
        model = Note
        fields = (
            "id",
            "author",
            "folder",
            "tags",
            "title",
            "content",
            "likes",
            "views",
            "create_time",
            "update_time",
        )


class UserNoteDetailSerializer(serializers.ModelSerializer):
    """个人笔记：详情"""

    author = AuthorSerializer()
    folder = NoteFolderSerializer()
    tag = NoteTagSerializer()

    class Meta:
        model = Note
        fields = (
            "id",
            "author",
            "folder",
            "is_private",
            "tag",
            "title",
            "content",
            "likes",
            "views",
            "create_time",
            "update_time",
        )


class NoteCommentsListSerializer(serializers.ModelSerializer):
    """评论：列表"""

    author = AuthorSerializer()

    class Meta:
        model = NoteComments
        fields = "__all__"


class UserNoteCommentsSerializer(serializers.ModelSerializer):
    """用户评论：创建、删除"""

    class Meta:
        model = NoteComments
        fields = ["id", "content", "note", "to_comment"]


class NoteTagHaystackSerializer(haystack_serializers.HaystackSerializer):
    """笔记标签搜索：列表"""

    object = NoteTagSerializer(read_only=True)

    class Meta:
        index_classes = [NoteTagIndex]
        search_fields = ["text"]
        fields = ["object"]


class NoteHaystackSerializer(haystack_serializers.HaystackSerializer):
    """笔记搜索：列表"""

    object = NoteListSerializer(read_only=True)

    class Meta:
        index_classes = [NoteIndex]
        search_fields = ["text"]
        fields = ["object"]
