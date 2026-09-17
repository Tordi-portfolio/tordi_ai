from django.contrib.auth.models import AbstractUser
from django.db import models


class TordiUser(AbstractUser):
    """Custom user for Tordi. Email is required and unique."""

    THEME_CHOICES = [
        ("light", "Light"),
        ("dark", "Dark"),
        ("brown", "Brown"),
    ]

    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    theme_preference = models.CharField(
        max_length=10, choices=THEME_CHOICES, default="dark"
    )

    def __str__(self):
        return self.username
