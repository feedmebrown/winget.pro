# Generated by Django 3.2.20 on 2023-08-09 16:41

from django.db import migrations, models
import winget.models


class Migration(migrations.Migration):

    dependencies = [
        ('winget', '0004_improve_help_texts'),
    ]

    operations = [
        migrations.AlterField(
            model_name='installer',
            name='file',
            field=models.FileField(upload_to=winget.models.installer_upload_to),
        ),
    ]
