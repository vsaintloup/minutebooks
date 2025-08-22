from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # Étendable (langue, cabinet, etc.)
    preferred_language = models.CharField(max_length=5, default="fr")
