from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0007_alter_postimage_options_postimage_caption_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="arxiv_url",
            field=models.URLField(blank=True, help_text="arXiv 논문 URL"),
        ),
        migrations.AddField(
            model_name="post",
            name="venue",
            field=models.CharField(blank=True, help_text="학회/저널명 (NeurIPS, ICML 등)", max_length=100),
        ),
        migrations.AddField(
            model_name="post",
            name="paper_year",
            field=models.IntegerField(blank=True, null=True, help_text="논문 발표 연도"),
        ),
        migrations.AddField(
            model_name="post",
            name="paper_authors",
            field=models.TextField(blank=True, help_text="저자 목록"),
        ),
    ]
