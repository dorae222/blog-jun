from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    code = models.CharField(max_length=20, blank=True, help_text="e.g. 10.Cloud")
    icon = models.CharField(max_length=50, blank=True, help_text="Icon name or emoji")
    color = models.CharField(max_length=7, blank=True, help_text="Hex color e.g. #3B82F6")
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children'
    )
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Series(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'series'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'

    class PostType(models.TextChoices):
        ARTICLE = 'article', 'Article'
        PAPER_REVIEW = 'paper_review', 'Paper Review'
        TUTORIAL = 'tutorial', 'Tutorial'
        TIL = 'til', 'TIL'
        PROJECT = 'project', 'Project'
        ACTIVITY_LOG = 'activity_log', 'Activity Log'

    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True)
    content = models.TextField()
    summary = models.TextField(blank=True, max_length=500)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    series = models.ForeignKey(
        Series, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts'
    )
    series_order = models.IntegerField(default=0)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    post_type = models.CharField(max_length=20, choices=PostType.choices, default=PostType.ARTICLE)
    quality_score = models.FloatField(default=0.0, help_text="AI-assessed quality 0-10")
    source_path = models.CharField(max_length=500, blank=True, help_text="Original file path")
    reading_time = models.IntegerField(default=0, help_text="Estimated reading time in minutes")
    view_count = models.IntegerField(default=0)
    pdf_file = models.FileField(
        upload_to='posts/pdfs/',
        blank=True,
        null=True,
        help_text="포스트에 첨부할 PDF 파일",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-published_at']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['post_type']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        if not self.reading_time and self.content:
            word_count = len(self.content.split())
            self.reading_time = max(1, word_count // 200)
        super().save(*args, **kwargs)


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    image = models.ImageField(upload_to='posts/%Y/%m/')
    alt_text = models.CharField(max_length=300, blank=True)
    original_path = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.alt_text or self.image.name


class PostTemplate(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    content_template = models.TextField(help_text="Markdown template content")
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True
    )
    post_type = models.CharField(
        max_length=20, choices=Post.PostType.choices, default=Post.PostType.ARTICLE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
