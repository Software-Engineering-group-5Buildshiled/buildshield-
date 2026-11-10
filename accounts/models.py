from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """A BuildShield user. The role decides what each user may do."""

    class Role(models.TextChoices):
        DEVELOPER = "DEV", "Developer"
        ANALYST = "ANALYST", "Security Analyst"
        ADMIN = "ADMIN", "Administrator"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.DEVELOPER)

    @property
    def is_analyst(self):
        return self.role == self.Role.ANALYST

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
