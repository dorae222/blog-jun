from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User

from blog.managers import PostManager


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
    categories = models.ManyToManyField(
        Category, blank=True, related_name='cross_posts',
        help_text="추가 카테고리 (다중 분류)"
    )
    series = models.ForeignKey(
        Series, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts'
    )
    series_order = models.IntegerField(default=0)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    post_type = models.CharField(max_length=20, choices=PostType.choices, default=PostType.ARTICLE)
    # 논문 리뷰 메타데이터 (post_type='paper_review'에서 사용)
    arxiv_url = models.URLField(blank=True, help_text="arXiv 논문 URL")
    venue = models.CharField(max_length=100, blank=True, help_text="학회/저널명 (NeurIPS, ICML 등)")
    paper_year = models.IntegerField(null=True, blank=True, help_text="논문 발표 연도")
    paper_authors = models.TextField(blank=True, help_text="저자 목록")

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
    cover_image = models.ImageField(
        upload_to='posts/covers/',
        blank=True,
        null=True,
        help_text="게시판 목록에 표시할 표지 이미지",
    )
    is_pinned = models.BooleanField(default=False, help_text="목록 상단 고정")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    objects = PostManager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-published_at']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['post_type']),
            models.Index(fields=['slug']),
            models.Index(fields=['author', 'status']),
            models.Index(fields=['is_pinned', '-published_at']),
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


def dynamic_upload_path(instance, filename):
    slug = instance.post.slug if instance.post else 'orphan'
    type_map = {
        'paper_figure': f'figures/papers/{slug}/{filename}',
        'code_output': f'figures/outputs/{slug}/{filename}',
        'diagram': f'figures/diagrams/{slug}/{filename}',
    }
    return type_map.get(instance.image_type, f'posts/{slug}/{filename}')


class PostImage(models.Model):
    IMAGE_TYPES = [
        ('general', '일반'),
        ('paper_figure', '논문 Figure'),
        ('code_output', '코드 실행 결과'),
        ('diagram', '다이어그램'),
    ]
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    image = models.ImageField(upload_to=dynamic_upload_path)
    image_type = models.CharField(max_length=20, choices=IMAGE_TYPES, default='general')
    caption = models.TextField(blank=True)
    source_ref = models.CharField(max_length=200, blank=True, help_text="e.g. Figure 3 from [Paper]")
    order = models.IntegerField(default=0)
    alt_text = models.CharField(max_length=300, blank=True)
    original_path = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

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


class PostLink(models.Model):
    """Obsidian [[]] wiki-link에서 추출한 포스트 간 관계."""
    from_post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='outgoing_links')
    to_post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='incoming_links')
    link_text = models.CharField(max_length=255, help_text="원본 [[텍스트]]")
    context = models.TextField(blank=True, help_text="링크가 사용된 주변 문맥")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_post', 'to_post')

    def __str__(self):
        return f"{self.from_post.slug} → {self.to_post.slug}"


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
    param_scale = models.CharField(max_length=200, blank=True, help_text="e.g. 8B parameters")
    context_length = models.CharField(max_length=200, blank=True, help_text="e.g. 128K tokens")

    # 아키텍처 상세
    attention_type = models.CharField(max_length=200, blank=True, help_text="e.g. GQA + RoPE")
    normalization = models.CharField(max_length=200, blank=True, help_text="e.g. RMSNorm (Pre-Norm)")
    activation = models.CharField(max_length=200, blank=True, help_text="e.g. SiLU (SwiGLU)")
    position_encoding = models.CharField(max_length=200, blank=True, help_text="e.g. RoPE")
    vocab_size = models.CharField(max_length=200, blank=True)
    hidden_dim = models.CharField(max_length=200, blank=True)
    num_layers = models.CharField(max_length=200, blank=True)
    num_heads = models.CharField(max_length=200, blank=True)

    # MoE 전용
    num_experts = models.CharField(max_length=200, blank=True, help_text="전문가 수 (dense 모델은 비워둠)")
    active_experts = models.CharField(max_length=200, blank=True)

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


class CloudServiceEntry(models.Model):
    class ServiceDomain(models.TextChoices):
        COMPUTE = 'compute', 'Compute'
        STORAGE = 'storage', 'Storage'
        DATABASE = 'database', 'Database'
        NETWORKING = 'networking', 'Networking'
        SECURITY = 'security', 'Security'
        ANALYTICS = 'analytics', 'Analytics'
        AI_ML = 'ai_ml', 'AI/ML'
        DEVTOOLS = 'devtools', 'DevTools'
        MANAGEMENT = 'management', 'Management'
        INTEGRATION = 'integration', 'Integration'
        CONTAINER = 'container', 'Container'
        DEVOPS = 'devops', 'DevOps'

    class Provider(models.TextChoices):
        AWS = 'aws', 'AWS'
        DOCKER = 'docker', 'Docker'
        LXD = 'lxd', 'LXD'
        GENERAL = 'general', 'General'

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    provider = models.CharField(
        max_length=20, choices=Provider.choices, default=Provider.AWS
    )
    service_domain = models.CharField(max_length=20, choices=ServiceDomain.choices)
    launch_year = models.IntegerField(null=True, blank=True)
    is_serverless = models.BooleanField(default=False)
    is_managed = models.BooleanField(default=True)
    pricing_model = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    key_detail = models.TextField(blank=True)
    use_cases = models.TextField(blank=True)
    docs_url = models.URLField(blank=True)
    icon_name = models.CharField(max_length=100, blank=True)
    importance = models.IntegerField(default=5)
    tree_x = models.FloatField(null=True, blank=True)
    tree_y = models.FloatField(null=True, blank=True)
    related_post = models.ForeignKey(
        'Post', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='cloud_service_entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['service_domain', 'name']
        verbose_name_plural = 'cloud service entries'

    def __str__(self):
        return f"{self.name} ({self.get_service_domain_display()})"


class CloudServiceRelation(models.Model):
    class RelationType(models.TextChoices):
        INTEGRATES_WITH = 'integrates_with', 'Integrates'
        DEPENDS_ON = 'depends_on', 'Depends On'
        ALTERNATIVE_TO = 'alternative_to', 'Alternative'
        PART_OF = 'part_of', 'Part Of'
        EVOLVED_FROM = 'evolved_from', 'Evolved From'

    from_service = models.ForeignKey(
        CloudServiceEntry, related_name='outgoing_relations', on_delete=models.CASCADE
    )
    to_service = models.ForeignKey(
        CloudServiceEntry, related_name='incoming_relations', on_delete=models.CASCADE
    )
    relation_type = models.CharField(max_length=20, choices=RelationType.choices)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('from_service', 'to_service', 'relation_type')

    def __str__(self):
        return f"{self.from_service.slug} → {self.to_service.slug} ({self.get_relation_type_display()})"
