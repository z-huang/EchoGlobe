from django.db import models
from django.utils import timezone


class Settings(models.Model):
    key = models.CharField(max_length=255, unique=True, db_index=True)
    value = models.CharField(max_length=255)

    class Meta:
        db_table = 'settings'


class Meeting(models.Model):
    topic = models.CharField(max_length=255, db_index=True, blank=True)
    date = models.DateField(default=timezone.now)
    audio_file = models.CharField(max_length=255, blank=True, null=True)  # MinIO path

    class Meta:
        db_table = 'meetings'


class MeetingContent(models.Model):
    meeting = models.ForeignKey(Meeting, related_name='contents', on_delete=models.CASCADE)
    block_id = models.IntegerField()
    message = models.TextField()
    time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'meeting_contents'
        ordering = ['block_id'] 