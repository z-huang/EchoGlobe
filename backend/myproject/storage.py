from minio import Minio
from django.conf import settings
import io


class MinioStorage:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        # Ensure bucket exists
        if not self.client.bucket_exists(settings.MINIO_BUCKET_NAME):
            self.client.make_bucket(settings.MINIO_BUCKET_NAME)

    def upload_audio(self, meeting_id: int, audio_data: bytes, content_type: str = 'audio/webm') -> str:
        """Upload audio data to MinIO and return the object name"""
        object_name = f"meeting_{meeting_id}/audio.webm"
        self.client.put_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=object_name,
            data=io.BytesIO(audio_data),
            length=len(audio_data),
            content_type=content_type
        )
        return object_name

    def get_audio(self, object_name: str) -> bytes:
        """Get audio data from MinIO"""
        try:
            response = self.client.get_object(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=object_name
            )
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete_audio(self, object_name: str):
        """Delete audio file from MinIO"""
        self.client.remove_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=object_name
        ) 