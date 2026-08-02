from django.db import models
from django.utils import timezone


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('locked', 'Locked'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    ]

    title = models.CharField(max_length=255)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    estimated_time = models.IntegerField()  # minutes
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    locked_until = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def deadline(self):
        """Deadline only applies to tasks created at an odd minute."""
        if self.created_at.minute % 2 != 0:
            return self.created_at + timezone.timedelta(minutes=self.estimated_time)
        return None

    @property
    def is_expired(self):
        deadline = self.deadline
        if deadline and timezone.now() > deadline and self.status not in ('completed',):
            return True
        return False

    def get_current_status(self):
        """Compute the effective status, checking lock expiry and odd-minute expiry."""
        if self.status == 'completed':
            return 'completed'
        if self.status == 'locked' and self.locked_until:
            if timezone.now() >= self.locked_until:
                return 'pending'
        if self.is_expired:
            return 'expired'
        return self.status


class Profile(models.Model):
    """Singleton profile record for the board owner."""
    name = models.CharField(max_length=120, default='Joel D.')
    email = models.EmailField(max_length=254, blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, default='')
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    dob = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Profile'

    def __str__(self):
        return self.name

    @classmethod
    def get_profile(cls):
        profile, _ = cls.objects.get_or_create(pk=1)
        return profile

    def initials(self):
        parts = self.name.strip().split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return self.name[:2].upper() if self.name else 'U'
