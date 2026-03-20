# Generated manually for Architecture tree expansion

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0003_architectureconcept_architectureentry"),
    ]

    operations = [
        # 1) Expand decoder_type choices
        migrations.AlterField(
            model_name="architectureentry",
            name="decoder_type",
            field=models.CharField(
                choices=[
                    ("dense", "Dense"),
                    ("sparse_moe", "Sparse MoE"),
                    ("sparse_hybrid", "Sparse Hybrid"),
                    ("ssm", "State Space Model"),
                    ("hybrid_ssm", "Hybrid SSM"),
                    ("diffusion_unet", "Diffusion (U-Net)"),
                    ("diffusion_dit", "Diffusion (DiT)"),
                    ("vision_encoder", "Vision Encoder"),
                    ("multimodal", "Multimodal LLM"),
                    ("technique", "Technique"),
                ],
                default="dense",
                max_length=20,
            ),
        ),
        # 2) Add architecture_category
        migrations.AddField(
            model_name="architectureentry",
            name="architecture_category",
            field=models.CharField(
                choices=[
                    ("llm", "LLM"),
                    ("ssm", "SSM"),
                    ("diffusion", "Diffusion"),
                    ("multimodal", "Multimodal"),
                    ("agent", "Agent"),
                    ("technique", "Technique"),
                    ("vision", "Vision"),
                ],
                default="llm",
                max_length=20,
            ),
        ),
        # 3) Add branch_type
        migrations.AddField(
            model_name="architectureentry",
            name="branch_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("encoder_only", "Encoder-Only"),
                    ("encoder_decoder", "Encoder-Decoder"),
                    ("decoder_only", "Decoder-Only"),
                    ("ssm", "SSM"),
                    ("diffusion", "Diffusion"),
                    ("vision", "Vision"),
                    ("multimodal", "Multimodal"),
                    ("agent", "Agent"),
                ],
                help_text="트리 시각화에서의 가지 위치",
                max_length=30,
            ),
        ),
        # 4) Add tree_x, tree_y
        migrations.AddField(
            model_name="architectureentry",
            name="tree_x",
            field=models.FloatField(blank=True, help_text="트리 X 좌표", null=True),
        ),
        migrations.AddField(
            model_name="architectureentry",
            name="tree_y",
            field=models.FloatField(blank=True, help_text="트리 Y 좌표", null=True),
        ),
        # 5) Add is_open_source
        migrations.AddField(
            model_name="architectureentry",
            name="is_open_source",
            field=models.BooleanField(default=True),
        ),
        # 6) Create ArchitectureRelation model
        migrations.CreateModel(
            name="ArchitectureRelation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "relation_type",
                    models.CharField(
                        choices=[
                            ("evolved_from", "발전"),
                            ("inspired_by", "영향"),
                            ("variant_of", "변형"),
                            ("technique_used", "기법 적용"),
                        ],
                        default="evolved_from",
                        max_length=20,
                    ),
                ),
                ("description", models.CharField(blank=True, max_length=200)),
                (
                    "from_entry",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="child_relations",
                        to="blog.architectureentry",
                    ),
                ),
                (
                    "to_entry",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parent_relations",
                        to="blog.architectureentry",
                    ),
                ),
            ],
            options={
                "unique_together": {("from_entry", "to_entry", "relation_type")},
            },
        ),
    ]
