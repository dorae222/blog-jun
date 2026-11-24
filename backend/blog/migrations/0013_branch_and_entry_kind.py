"""가지를 데이터로 빼고 항목 종류를 나눈다.

`branch_type`이 TextChoices 8개로 코드에 박혀 있어서 가지를 하나 늘릴 때마다 코드 수정과
마이그레이션이 필요했다. 앞으로 검색·RAG·벡터 인덱스·프롬프트 최적화·그래프 ML·고전 ML·
서빙 일곱 갈래가 더 붙는다. 그래서 Branch 테이블로 뺀다.

`branch_type` 컬럼은 지우지 않는다. API 필터와 프론트엔드 네 곳이 그 문자열을 읽고 있어서,
지우면 그 화면들이 깨진다. 슬러그를 그대로 담는 거울로 남기고 정본은 FK로 옮긴다.

`entry_kind`도 함께 넣는다. 지금 노드는 전부 모델 카드인데 여기에 논문 리뷰를 얹으면
"모델"과 "논문"과 "기법"이 한 종류로 섞인다. 트리에서 모양과 필터를 가르려면 구분이 필요하다.
"""
from django.db import migrations, models
import django.db.models.deletion


# 기존 8개는 지금 데이터에 있는 값이고, 나머지 7개는 앞으로 쓸 자리다.
# 색은 pipeline/tree_layout.py의 LANE_COLOR와 맞춘다. 두 곳이 어긋나면 미리보기와
# 실제 화면의 색이 달라진다.
SEED = [
    # (slug, name, color, order, axis)
    ('encoder_only',    '인코더 전용',   '#dc2626',  10, 'branch'),
    ('encoder_decoder', '인코더-디코더', '#059669',  20, 'branch'),
    ('decoder_only',    '디코더 전용',   '#2563eb',  30, 'trunk'),
    ('ssm',             '상태공간 모델', '#7c3aed',  40, 'branch'),
    ('multimodal',      '멀티모달',      '#ea580c',  50, 'branch'),
    ('vision',          '비전',          '#0891b2',  60, 'branch'),
    ('diffusion',       '디퓨전',        '#db2777',  70, 'branch'),
    ('agent',           '에이전트',      '#65a30d',  80, 'branch'),
    # 새 가지. 논문 시리즈가 여기에 붙는다.
    ('retrieval',       '검색·임베딩',   '#0d9488',  90, 'branch'),
    ('rag',             'RAG',           '#4f46e5', 100, 'branch'),
    ('vector_index',    '벡터 인덱스',   '#7c2d12', 110, 'branch'),
    ('prompt_opt',      '프롬프트 최적화', '#a21caf', 120, 'branch'),
    ('graph_ml',        '그래프 ML',     '#0369a1', 130, 'branch'),
    ('classic_ml',      '고전 ML',       '#78716c', 140, 'branch'),
    ('serving',         '서빙',          '#b45309', 150, 'branch'),
]


def seed_branches(apps, schema_editor):
    Branch = apps.get_model('blog', 'Branch')
    Entry = apps.get_model('blog', 'ArchitectureEntry')

    by_slug = {}
    for slug, name, color, order, axis in SEED:
        b, _ = Branch.objects.get_or_create(
            slug=slug,
            defaults={'name': name, 'color': color, 'order': order, 'axis': axis},
        )
        by_slug[slug] = b

    # 기존 문자열을 FK로 옮긴다. 값이 비어 있거나 모르는 슬러그면 건드리지 않는다.
    # 실제로 8개 항목이 branch_type 없이 들어와 있어서, 그것들은 그대로 둔다.
    for e in Entry.objects.exclude(branch_type='').iterator():
        b = by_slug.get(e.branch_type)
        if b is not None:
            Entry.objects.filter(pk=e.pk).update(branch=b)


def unseed(apps, schema_editor):
    # branch_type이 거울로 남아 있으므로 FK만 끊으면 원래 상태다.
    Entry = apps.get_model('blog', 'ArchitectureEntry')
    Entry.objects.update(branch=None)
    apps.get_model('blog', 'Branch').objects.filter(
        slug__in=[s for s, *_ in SEED]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0012_series_cover_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='Branch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60)),
                ('slug', models.SlugField(unique=True)),
                ('color', models.CharField(default='#64748b', max_length=7)),
                ('order', models.IntegerField(default=0, help_text='트리에서 왼쪽부터의 순서')),
                ('axis', models.CharField(
                    choices=[('trunk', '줄기'), ('branch', '가지')],
                    default='branch', max_length=10)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'verbose_name_plural': 'branches',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.AddField(
            model_name='architectureentry',
            name='branch',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='entries', to='blog.branch',
                help_text='트리에서의 가지. 정본은 이쪽이다'),
        ),
        migrations.AddField(
            model_name='architectureentry',
            name='entry_kind',
            field=models.CharField(
                choices=[('model', '모델'), ('paper', '논문'), ('technique', '기법')],
                default='model', max_length=20,
                help_text='모델 카드인지 논문 리뷰인지 기법인지. 트리에서 모양과 필터가 갈린다'),
        ),
        migrations.AlterField(
            model_name='architectureentry',
            name='branch_type',
            field=models.CharField(
                blank=True, max_length=30,
                help_text='branch.slug의 사본. 직접 고치지 마라. save()가 branch에서 맞춘다'),
        ),
        migrations.RunPython(seed_branches, unseed),
    ]
