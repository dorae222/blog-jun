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
    cover_image = models.ImageField(
        upload_to='series/covers/',
        blank=True,
        null=True,
        help_text="시리즈 묶음 표지 - 없으면 첫 편의 표지로 대체한다",
    )
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


class Branch(models.Model):
    """계보 트리의 가지.

    원래 `ArchitectureEntry.branch_type`이 `TextChoices` 8개로 코드에 박혀 있었다.
    가지를 하나 늘릴 때마다 코드 수정과 마이그레이션이 필요했는데, 가지는 데이터다.
    검색·RAG·벡터 인덱스·프롬프트 최적화·그래프 ML·고전 ML·서빙처럼 앞으로 늘어날
    갈래가 여럿이라 여기로 뺐다.

    `slug`가 키다. 기존 `branch_type` 문자열이 그대로 슬러그가 되므로 API가 안 깨진다.
    """
    class Axis(models.TextChoices):
        TRUNK = 'trunk', '줄기'
        BRANCH = 'branch', '가지'

    name = models.CharField(max_length=60)
    slug = models.SlugField(unique=True)
    color = models.CharField(max_length=7, default='#64748b')
    order = models.IntegerField(default=0, help_text="트리에서 왼쪽부터의 순서")
    axis = models.CharField(max_length=10, choices=Axis.choices, default=Axis.BRANCH)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'branches'

    def __str__(self):
        return self.name


class ArchitectureEntry(models.Model):
    class EntryKind(models.TextChoices):
        MODEL = 'model', '모델'
        PAPER = 'paper', '논문'
        TECHNIQUE = 'technique', '기법'

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
    branch = models.ForeignKey(
        Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='entries',
        help_text="트리에서의 가지. 정본은 이쪽이다"
    )
    # `branch`의 슬러그를 그대로 담는 거울 필드다. API와 필터가 오래전부터 이 이름을
    # 문자열로 써 왔고, 프론트엔드 네 곳이 그 값을 읽는다. 지우면 그 화면들이 깨진다.
    # `choices`는 뗐다. 가지가 늘 때마다 코드를 고치지 않으려고 Branch로 뺐기 때문이다.
    branch_type = models.CharField(
        max_length=30, blank=True,
        help_text="branch.slug의 사본. 직접 고치지 마라. save()가 branch에서 맞춘다"
    )
    entry_kind = models.CharField(
        max_length=20, choices=EntryKind.choices, default=EntryKind.MODEL,
        help_text=(
            "model=가중치나 API로 실제 서비스되는 모델 카드, "
            "paper=논문 한 편이 정본인 기법(CoT·ReAct·Reflexion 같은 것), "
            "technique=모델이 아닌 기법·프로토콜·프레임워크(LoRA·MCP·LangGraph). "
            "API의 tree/list/detail 세 serializer가 모두 실어 보낸다"
        )
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

    def save(self, *args, **kwargs):
        # 거울 필드를 한 곳에서만 쓴다. 두 값이 어긋나면 필터와 화면이 서로 다른 말을 한다.
        # branch를 비운 채 branch_type만 넣고 저장하는 옛 코드가 있어서, 그 경우에는
        # 슬러그로 branch를 찾아 채워 준다. 없는 슬러그면 문자열만 남긴다.
        if self.branch_id:
            self.branch_type = self.branch.slug
        elif self.branch_type:
            self.branch = Branch.objects.filter(slug=self.branch_type).first()
        update_fields = kwargs.get('update_fields')
        if update_fields is not None:
            uf = set(update_fields)
            if 'branch' in uf or 'branch_type' in uf:
                kwargs['update_fields'] = list(uf | {'branch', 'branch_type'})
        super().save(*args, **kwargs)

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

    class Layer(models.TextChoices):
        """추상화 층. 인프라 트리의 세로축이다.

        `launch_year` 를 세로축으로 쓰지 않는다. 인프라 기술의 값은 언제 나왔느냐가
        아니라 어느 층에 서느냐에 있다. EC2(2006)와 Fargate(2017)를 연도로 세우면
        둘 다 컴퓨트라는 것만 보이고, 층으로 세우면 가상화 위에 서버리스가 얹힌
        관계가 보인다.

        위가 추상이고 아래가 물리다. `CONCEPT` 만 층이 아니라 층 밖이다.
        MVCC·CIDR·GitOps 처럼 제품이 아닌 규격과 기법이 여기 선다.
        """
        CONCEPT = 'concept', '개념·규격'
        SERVERLESS = 'serverless', '서버리스'
        MANAGED = 'managed', '관리형'
        ORCHESTRATION = 'orchestration', '오케스트레이션'
        CONTAINER = 'container', '컨테이너'
        VIRTUALIZATION = 'virtualization', '가상화'
        PHYSICAL = 'physical', '물리·OS'

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    provider = models.CharField(
        max_length=20, choices=Provider.choices, default=Provider.AWS
    )
    service_domain = models.CharField(max_length=20, choices=ServiceDomain.choices)
    launch_year = models.IntegerField(null=True, blank=True)
    layer = models.CharField(
        max_length=20, choices=Layer.choices, blank=True, default='',
        help_text='추상화 층. 인프라 트리의 세로축이다. 위가 추상, 아래가 물리다',
    )
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
        # 아래 둘은 **층을 가로지르는 세로선**이다. 나머지 다섯에는 층을 건너는
        # 뜻이 없었다. PostgreSQL(물리) -> RDS(관리형)가 managed_version_of 이고
        # Docker(컨테이너) -> Linux(물리)가 runs_on 이다. alternative_to 는 같은 층
        # 안의 가로선이라 선 방향만 봐도 무슨 관계인지 읽힌다.
        RUNS_ON = 'runs_on', 'Runs On'
        MANAGED_VERSION_OF = 'managed_version_of', 'Managed Version Of'

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
