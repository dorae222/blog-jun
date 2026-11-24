"""인프라 트리에 세로축을 준다.

왜 필요한가
  `/architectures/tree?domain=cloud` 는 AI 쪽과 달리 계보가 아니라 힘배치였다.
  노드 63개가 관계로 뭉쳐 떠다니고 63개 중 32개에는 좌표조차 없었다. 원인은 세로축이
  없다는 것이다. AI 트리는 `release_date` 의 연도가 세로를 정하는데 인프라 쪽에는
  대응하는 축이 없었다.

  `launch_year` 를 쓰면 안 된다. 인프라 기술의 값은 출시 시점이 아니라 **어느 추상화
  층에 서느냐**에 있다. EC2(2006)와 Fargate(2017)를 연도로 세우면 "둘 다 컴퓨트"라는
  것만 보이고, 층으로 세우면 가상화 위에 서버리스가 얹힌 관계가 보인다.
  `docs/infra-tree-gap-2026-08.md` 7절이 206개 후보의 층 분포를 재어 같은 결론을 냈다.

왜 테이블이 아니라 choices 인가
  가지(`Branch`)는 테이블로 뺐다. 갈래가 계속 늘어서였다. 층은 다르다. 물리에서
  서버리스까지 일곱은 닫힌 개념 집합이고 늘어날 자리가 없다. 조인을 하나 더 두는 값이
  안 나온다. 늘어나는 쪽은 `service_domain` 이고 그쪽은 다음 과제다.

관계 두 종류
  `runs_on` 과 `managed_version_of` 는 **층을 가로지르는 세로선**이다.
  PostgreSQL(물리) -> RDS(관리형)가 후자이고, Docker(컨테이너) -> Linux(물리)가 전자다.
  기존 다섯 종류에는 층을 건너는 뜻이 없었다. `alternative_to` 는 같은 층 안의 가로선이라
  선 방향만 봐도 무슨 관계인지 읽힌다.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0014_entry_kind_help_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='cloudserviceentry',
            name='layer',
            field=models.CharField(
                blank=True,
                choices=[
                    ('concept', '개념·규격'),
                    ('serverless', '서버리스'),
                    ('managed', '관리형'),
                    ('orchestration', '오케스트레이션'),
                    ('container', '컨테이너'),
                    ('virtualization', '가상화'),
                    ('physical', '물리·OS'),
                ],
                default='',
                help_text='추상화 층. 인프라 트리의 세로축이다. 위가 추상, 아래가 물리다',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='cloudservicerelation',
            name='relation_type',
            field=models.CharField(
                choices=[
                    ('integrates_with', 'Integrates'),
                    ('depends_on', 'Depends On'),
                    ('alternative_to', 'Alternative'),
                    ('part_of', 'Part Of'),
                    ('evolved_from', 'Evolved From'),
                    ('runs_on', 'Runs On'),
                    ('managed_version_of', 'Managed Version Of'),
                ],
                max_length=20,
            ),
        ),
    ]
