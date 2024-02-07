from rest_framework import serializers
from drf_haystack import serializers as haystack_serializers

from note.models import Note, NoteTag, NoteComments
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
        model = NoteTag
        fields = "__all__"


class UserNoteListSerializer(serializers.ModelSerializer):
    """用户笔记：列表"""

    tag = NoteTagSerializer()

    class Meta:
        model = Note
        fields = ("id", "tag", "title", "views", "likes", "is_private")


class NoteListSerializer(serializers.ModelSerializer):
    """笔记：列表（大厅）"""

    class Meta:
        model = Note
        fields = ("id", "title", "views", "likes")


class UserNoteSerializer(serializers.ModelSerializer):
    """个人笔记：创建、更新、删除"""

    class Meta:
        model = Note
        fields = ("id", "tag", "title", "is_private", "folder", "content")

    def validate_folder(self, value):
        user = self.context["request"].user
        if value and value.user != user:
            raise serializers.ValidationError('非法的文件夹！')
        return value
    
    def validate(self, data):
        user = self.context["request"].user
        if Note.objects.filter(author=user, folder=data['folder'], title=data['title']).exists():
            raise serializers.ValidationError({'title':['该标题在该文件夹中已存在！']})
        return data


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
    tag = NoteTagSerializer()

    class Meta:
        model = Note
        fields = (
            "id",
            "author",
            "folder",
            "tag",
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
        fields = ['object']


class NoteHaystackSerializer(haystack_serializers.HaystackSerializer):
    """笔记搜索：列表"""
    object = NoteListSerializer(read_only=True)
    class Meta:
        index_classes = [NoteIndex]
        search_fields = ["text"]
        fields = ['object']


