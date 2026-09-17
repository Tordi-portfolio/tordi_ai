from django.conf import settings
from django.db import models


def chat_image_path(instance, filename):
    return f"uploads/images/{instance.conversation.user_id}/{filename}"


def chat_audio_path(instance, filename):
    return f"uploads/audio/{instance.conversation.user_id}/{filename}"


class Conversation(models.Model):
    """A single chat thread, shown in the sidebar."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations"
    )
    title = models.CharField(max_length=255, default="New chat")
    pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-pinned", "-updated_at"]

    def __str__(self):
        return f"{self.title} ({self.user})"


class Message(models.Model):
    ROLE_CHOICES = [("user", "User"), ("assistant", "Tordi")]

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to=chat_image_path, blank=True, null=True)
    audio = models.FileField(upload_to=chat_audio_path, blank=True, null=True)
    edited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.role}] {self.content[:40]}"
