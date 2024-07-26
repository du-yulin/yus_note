from django.db import models
from django.conf import settings
from tinymce.models import HTMLField

from yus_note.models import ReviewMixinModel, cached_model_property


class Category(models.Model):
    """
    笔记分类
    """

    name = models.CharField(
        "名称",
        max_length=32,
    )

    class Meta:
        verbose_name = "笔记分类"
        verbose_name_plural = verbose_name
        db_table = "note_category"
        constraints = [
            models.UniqueConstraint(fields=["name"], name="note_category_uni_name")
        ]

    def __str__(self) -> str:
        return "{}".format(self.name)


class Tag(models.Model):
    """
    笔记标签模型
    """

    name = models.CharField(
        "名称",
        max_length=32,
    )

    class Meta:
        verbose_name = "笔记标签"
        verbose_name_plural = verbose_name
        db_table = "note_tag"
        constraints = [
            models.UniqueConstraint(fields=["name"], name="note_tag_uni_name")
        ]

    def __str__(self) -> str:
        return "{}".format(self.name)


def set_default_category() -> Category:
    return Category.objects.get_or_create(name="其他")[0]


class NoteTags(models.Model):
    """
    笔记-笔记标签中间表
    """

    note = models.ForeignKey(
        verbose_name="笔记",
        to="Note",
        related_name="note_tags",
        on_delete=models.CASCADE,
        limit_choices_to={"is_delete": False},
    )
    tag = models.ForeignKey(
        verbose_name="标签",
        to=Tag,
        related_name="note_tags",
        on_delete=models.CASCADE,
    )
    category = models.ForeignKey(
        verbose_name="类别",
        to=Category,
        related_name="note_tags",
        on_delete=models.SET(set_default_category),  # type: ignore
    )

    class Meta:
        verbose_name = "笔记-笔记标签"
        verbose_name_plural = verbose_name
        db_table = "note_note_tags"

    def __str__(self) -> str:
        return "{}:{}".format(self.note, self.tag)


def set_default_tag() -> Tag:
    return Tag.objects.get_or_create(
        name=getattr(settings, "DEFAULT_NOTE_TAG_NAME", "其他")
    )[0]


class Note(ReviewMixinModel, models.Model):
    """
    笔记模型
    """

    author = models.ForeignKey(
        "user.User",
        verbose_name="作者",
        related_name="self_notes",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"is_active": True},
    )
    folder = models.ForeignKey(
        verbose_name="所属文件夹",
        to="user.UserFolders",
        related_name="notes",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        verbose_name="笔记分类",
        to=Category,
        on_delete=models.SET(set_default_category),  # type: ignore
    )
    tags = models.ManyToManyField(
        verbose_name="标签",
        to=Tag,
        related_name="notes",
        blank=True,
        through=NoteTags,
        through_fields=("note", "tag"),
    )
    title = models.CharField("主题", max_length=32)
    is_private = models.BooleanField("是否私有", default=False)
    content = HTMLField("内容")
    likes = models.PositiveIntegerField("点赞数", default=0)
    views = models.PositiveIntegerField("浏览量", default=0)
    create_time = models.DateTimeField("创建时间", auto_now_add=True)
    update_time = models.DateTimeField("最近更新时间", auto_now=True)
    is_delete = models.BooleanField("是否已删除", default=False)
    delete_date = models.DateField("删除时间", null=True, blank=True)

    class Meta:
        verbose_name = "笔记"
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(
                fields=["-create_time"], name="note_note_idx_create_time_desc"
            ),
            models.Index(fields=["-views"], name="note_note_idx_views_desc"),
        ]

    @cached_model_property(cache="model_fields", expires={"days": 1}, at="03:00:00")
    def cached_views(self):
        return self.views

    def __str__(self) -> str:
        return "{}".format(self.title)


class NoteComments(models.Model):
    content = models.CharField("内容", max_length=120)
    note = models.ForeignKey(
        verbose_name="笔记",
        to=Note,
        related_name="comments",
        on_delete=models.CASCADE,
        limit_choices_to={"is_delete": False},
    )
    author = models.ForeignKey(
        "user.User",
        verbose_name="作者",
        related_name="comments",
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={"is_active": True},
    )
    to_comment = models.ForeignKey(
        "self",
        verbose_name="所回复的评论",
        related_name="comments",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    create_time = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "笔记评论"
        db_table = "note_comments"
        indexes = [
            models.Index(fields=["create_time"], name="note_comments_idx_create_time")
        ]

    def __str__(self) -> str:
        return f'{self.note.title}/{self.author.username}{"回复:"+self.to_comment.content if self.to_comment else ""}:{self.content}'  # type: ignore
