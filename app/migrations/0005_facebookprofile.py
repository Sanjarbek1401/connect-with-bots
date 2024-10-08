# Generated by Django 5.1.1 on 2024-10-09 09:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_instagramprofile'),
    ]

    operations = [
        migrations.CreateModel(
            name='FacebookProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('facebook_user_id', models.CharField(max_length=255)),
                ('username', models.CharField(max_length=255)),
                ('user_profile', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='app.userprofile')),
            ],
        ),
    ]
