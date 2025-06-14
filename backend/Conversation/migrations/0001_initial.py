# Generated by Django 5.2.1 on 2025-05-27 01:52

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(blank=True, unique=True)),
                ('title', models.CharField(max_length=255)),
                ('src_language', models.CharField(help_text="Original language code, e.g., 'en', 'es'", max_length=10)),
                ('media_url', models.URLField(help_text='URL to the media file (stored externally)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('en_transcription', models.TextField(blank=True, help_text='English transcription of the media')),
                ('cn_transcription', models.TextField(blank=True, help_text='Chinese transcription of the media')),
                ('de_transcription', models.TextField(blank=True, help_text='German transcription of the media')),
                ('jp_transcription', models.TextField(blank=True, help_text='Japanese transcription of the media')),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conversations', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
