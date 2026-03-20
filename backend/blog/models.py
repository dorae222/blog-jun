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


class ArchitectureConcept(models.Model):
    """MHA, GQA, MLA, RoPE, QK-Norm, SWA, MoE 등 아키텍처 개념 태그"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    abbreviation = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#6366F1')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.abbreviation or self.name


class ArchitectureEntry(models.Model):
    class DecoderType(models.TextChoices):
        DENSE = 'dense', 'Dense'
        SPARSE_MOE = 'sparse_moe', 'Sparse MoE'
        SPARSE_HYBRID = 'sparse_hybrid', 'Sparse Hybrid'
        SSM = 'ssm', 'State Space Model'
        HYBRID_SSM = 'hybrid_ssm', 'Hybrid SSM'
        DIFFUSION_UNET = 'diffusion_unet', 'Diffusion (U-Net)'
        DIFFUSION_DIT = 'diffusion_dit', 'Diffusion (DiT)'
        VISION_ENCODER = 'vision_encoder', 'Vision Encoder'
        MULTIMODAL = 'multimodal', 'Multimodal LLM'
        TECHNIQUE = 'technique', 'Technique'

    class ArchitectureCategory(models.TextChoices):
        LLM = 'llm', 'LLM'
        SSM = 'ssm', 'SSM'
        DIFFUSION = 'diffusion', 'Diffusion'
        MULTIMODAL = 'multimodal', 'Multimodal'
        AGENT = 'agent', 'Agent'
        TECHNIQUE = 'technique', 'Technique'
        VISION = 'vision', 'Vision'

    class BranchType(models.TextChoices):
        ENCODER_ONLY = 'encoder_only', 'Encoder-Only'
        ENCODER_DECODER = 'encoder_decoder', 'Encoder-Decoder'
        DECODER_ONLY = 'decoder_only', 'Decoder-Only'
        SSM = 'ssm', 'SSM'
        DIFFUSION = 'diffusion', 'Diffusion'
        VISION = 'vision', 'Vision'
        MULTIMODAL = 'multimodal', 'Multimodal'
        AGENT = 'agent', 'Agent'

    # 기본 정보
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    organization = models.CharField(max_length=100)
    release_date = models.DateField(null=True, blank=True)

    # 분류
    decoder_type = models.CharField(max_length=20, choices=DecoderType.choices, default=DecoderType.DENSE)
    concepts = models.ManyToManyField(ArchitectureConcept, blank=True, related_name='entries')

    # 기본 스펙
    param_scale = models.CharField(max_length=50, blank=True, help_text="e.g. 8B parameters")
    context_length = models.CharField(max_length=50, blank=True, help_text="e.g. 128K tokens")

    # 아키텍처 상세
    attention_type = models.CharField(max_length=100, blank=True, help_text="e.g. GQA + RoPE")
    normalization = models.CharField(max_length=100, blank=True, help_text="e.g. RMSNorm (Pre-Norm)")
    activation = models.CharField(max_length=100, blank=True, help_text="e.g. SiLU (SwiGLU)")
    position_encoding = models.CharField(max_length=100, blank=True, help_text="e.g. RoPE")
    vocab_size = models.CharField(max_length=50, blank=True)
    hidden_dim = models.CharField(max_length=50, blank=True)
    num_layers = models.CharField(max_length=50, blank=True)
    num_heads = models.CharField(max_length=50, blank=True)

    # MoE 전용
    num_experts = models.CharField(max_length=50, blank=True, help_text="전문가 수 (dense 모델은 비워둠)")
    active_experts = models.CharField(max_length=50, blank=True)

    # 서술 필드
    description = models.TextField(blank=True, help_text="한글 설명")
    key_detail = models.TextField(blank=True, help_text="핵심 특징 한줄 요약")
    training_detail = models.TextField(blank=True, help_text="학습 관련 특이사항")

    # 링크
    paper_url = models.URLField(blank=True)
    code_url = models.URLField(blank=True)
    license_type = models.CharField(max_length=100, blank=True)

    # 트리 분류
    architecture_category = models.CharField(
        max_length=20, choices=ArchitectureCategory.choices, default=ArchitectureCategory.LLM
    )
    branch_type = models.CharField(
        max_length=30, choices=BranchType.choices, blank=True,
        help_text="트리 시각화에서의 가지 위치"
    )
    tree_x = models.FloatField(null=True, blank=True, help_text="트리 X 좌표")
    tree_y = models.FloatField(null=True, blank=True, help_text="트리 Y 좌표")
    is_open_source = models.BooleanField(default=True)

    # Figure
    figure = models.ImageField(upload_to='architectures/', blank=True, null=True)
    figure_placeholder = models.BooleanField(default=True)

    # 연결
    related_post = models.ForeignKey(
        'Post', on_delete=models.SET_NULL, null=True, blank=True, related_name='architecture_entries'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-release_date', 'name']
        verbose_name_plural = 'architecture entries'

    def __str__(self):
        return f"{self.name} ({self.organization})"


class ArchitectureRelation(models.Model):
    class RelationType(models.TextChoices):
        EVOLVED_FROM = 'evolved_from', '발전'
        INSPIRED_BY = 'inspired_by', '영향'
        VARIANT_OF = 'variant_of', '변형'
        TECHNIQUE_USED = 'technique_used', '기법 적용'

    from_entry = models.ForeignKey(
        ArchitectureEntry, related_name='child_relations', on_delete=models.CASCADE
    )
    to_entry = models.ForeignKey(
        ArchitectureEntry, related_name='parent_relations', on_delete=models.CASCADE
    )
    relation_type = models.CharField(
        max_length=20, choices=RelationType.choices, default=RelationType.EVOLVED_FROM
    )
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('from_entry', 'to_entry', 'relation_type')

    def __str__(self):
        return f"{self.from_entry.slug} → {self.to_entry.slug} ({self.get_relation_type_display()})"
