from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0011_cloudserviceentry'),
    ]

    operations = [
        migrations.AddField(
            model_name='series',
            name='cover_image',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='series/covers/',
                help_text='시리즈 묶음 표지 - 없으면 첫 편의 표지로 대체한다',
            ),
        ),
    ]
