from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='pdf_file',
            field=models.FileField(
                blank=True,
                help_text='포스트에 첨부할 PDF 파일',
                null=True,
                upload_to='posts/pdfs/',
            ),
        ),
    ]
