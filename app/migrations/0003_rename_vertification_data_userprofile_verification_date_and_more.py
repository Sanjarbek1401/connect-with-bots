# Generated by Django 5.1.1 on 2024-10-08 05:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_userprofile_is_verified_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userprofile',
            old_name='vertification_data',
            new_name='verification_date',
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='passport_number',
            field=models.CharField(blank=True, max_length=7, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='passport_series',
            field=models.CharField(blank=True, max_length=2, null=True),
        ),
    ]
