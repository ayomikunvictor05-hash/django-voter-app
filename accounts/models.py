from django.db import models

# Create your models here.

# accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    email_domain = models.CharField(max_length=100, blank=True)
    voter_group = models.CharField(max_length=100, blank=True, help_text="e.g., Science Dept, Regional Branch")

    def save(self, *args, **kwargs):
        if self.email and '@' in self.email:
            self.email_domain = self.email.split('@')[-1].lower()
        super().save(*args, **kwargs)