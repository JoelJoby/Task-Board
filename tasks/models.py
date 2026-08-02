from django.db import models
from django.utils import timezone
import random

DEFAULT_HINTS = [
    "Patience is a key written in shadow. The clock must speak '00:00' before the seal dissolves.",
    "The stars have not aligned. Wait for the celestial hands of time to turn.",
    "Shadows cannot step into the light before high noon.",
    "A secret phrase rests in the void. Speak the lost word to shatter the seal.",
    "The ancient hourglass still drips with sand. Do not rush destiny.",
    "The threshold remains closed to those who rush. Time itself holds the key.",
    "Echoes of incomplete time whisper: 'Not yet...'"
]

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    ]

    LOCK_TYPE_CHOICES = [
        ('NONE', 'No Lock'),
        ('COUNTDOWN', 'Time Countdown'),
        ('CODE', 'Secret Passcode'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    estimated_minutes = models.PositiveIntegerField(default=30)
    
    lock_type = models.CharField(max_length=15, choices=LOCK_TYPE_CHOICES, default='NONE')
    unlock_at = models.DateTimeField(blank=True, null=True)
    unlock_code = models.CharField(max_length=50, blank=True, default='')
    cryptic_hint = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.cryptic_hint:
            self.cryptic_hint = random.choice(DEFAULT_HINTS)
        super().save(*args, **kwargs)

    @property
    def is_currently_locked(self):
        if self.status == 'COMPLETED':
            return False
        if self.lock_type == 'COUNTDOWN' and self.unlock_at:
            return timezone.now() < self.unlock_at
        if self.lock_type == 'CODE':
            return True
        return False

    @property
    def remaining_seconds(self):
        if self.lock_type == 'COUNTDOWN' and self.unlock_at:
            delta = (self.unlock_at - timezone.now()).total_seconds()
            return max(0, int(delta))
        return 0

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'estimated_minutes': self.estimated_minutes,
            'lock_type': self.lock_type,
            'unlock_at': self.unlock_at.isoformat() if self.unlock_at else None,
            'cryptic_hint': self.cryptic_hint,
            'is_locked': self.is_currently_locked,
            'remaining_seconds': self.remaining_seconds,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'has_passcode': bool(self.unlock_code),
        }

    def __str__(self):
        return f"{self.title} ({self.get_priority_display()})"
