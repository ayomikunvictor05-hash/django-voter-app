# polls/models.py

import secrets
import qrcode
from io import BytesIO
from django.db import models
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone


def generate_unique_code():
    return secrets.token_hex(4).upper()


class Poll(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        ACTIVE = 'ACTIVE', 'Active'
        PAUSED = 'PAUSED', 'Paused'
        COMPLETED = 'COMPLETED', 'Completed'

    class ResultsVisibility(models.TextChoices):
        REALTIME = 'REALTIME', 'Real-Time Results'
        AFTER_END = 'AFTER_END', 'Results Visible After Poll Ends'

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_polls'
    )
    unique_code = models.CharField(
        max_length=12,
        unique=True,
        default=generate_unique_code,
        db_index=True
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    # Time Window Scheduling
    start_time = models.DateTimeField(
        default=timezone.now,
        help_text="The date and time when voting officially opens."
    )
    end_time = models.DateTimeField(
        help_text="The date and time when voting automatically closes."
    )

    results_visibility = models.CharField(
        max_length=15,
        choices=ResultsVisibility.choices,
        default=ResultsVisibility.REALTIME
    )
    passcode = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Optional secondary passcode required to access ballot."
    )
    allowed_domains = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated list of allowed email domains."
    )
    allowed_voter_group = models.CharField(
        max_length=100,
        blank=True,
        help_text="Restrict to users matching a specific voter group."
    )

    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_active(self):
        """Checks if current time falls within start_time and end_time."""
        now = timezone.now()
        return self.status == self.Status.ACTIVE and self.start_time <= now <= self.end_time

    def is_upcoming(self):
        """Checks if poll has been scheduled for a future time."""
        return timezone.now() < self.start_time

    def get_allowed_domains_list(self):
        if not self.allowed_domains:
            return []
        return [d.strip().lower().lstrip('@') for d in self.allowed_domains.split(',') if d.strip()]

    def save(self, *args, **kwargs):
        if not self.qr_code:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.unique_code)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            file_name = f'qr_{self.unique_code}.png'
            self.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} [{self.unique_code}]"


class Choice(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name='choices'
    )
    option_text = models.CharField(max_length=255)
    # Optional image upload per voting choice
    image = models.ImageField(upload_to='choice_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.option_text} ({self.poll.title})"


class Vote(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    choice = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    voter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='casted_votes'
    )
    receipt_token = models.CharField(
        max_length=64,
        unique=True,
        editable=False
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['poll', 'voter'],
                name='unique_user_vote_per_poll'
            )
        ]

    def save(self, *args, **kwargs):
        if not self.receipt_token:
            token = secrets.token_hex(4).upper()
            self.receipt_token = f"VOTE-{token[:4]}-{token[4:]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Receipt {self.receipt_token} for Poll {self.poll.unique_code}"