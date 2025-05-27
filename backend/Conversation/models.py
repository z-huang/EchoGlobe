from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils import timezone


User = get_user_model()

class Conversation(models.Model):
    slug = models.SlugField(unique=True, blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255)
    media_url = models.URLField(help_text="URL to the media file (stored externally)")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            # Use current time if created_at is None
            timestamp = self.created_at.timestamp() if self.created_at else timezone.now().timestamp()
            self.slug = slugify(f"{self.title}-{self.creator.id}-{timestamp}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Sentence(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='sentences')
    
    source_transcription = models.TextField(blank=True, help_text="Transcription of the original media")
    en_transcription = models.TextField(blank=True, help_text="English transcription of the media")
    cn_transcription = models.TextField(blank=True, help_text="Chinese transcription of the media")
    de_transcription = models.TextField(blank=True, help_text="German transcription of the media")
    jp_transcription = models.TextField(blank=True, help_text="Japanese transcription of the media")
    created_at = models.DateTimeField(auto_now_add=True)