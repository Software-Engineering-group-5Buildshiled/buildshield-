from django.conf import settings
from django.db import models
from django.utils import timezone


class SITFPillar(models.Model):
    """One of the five SITF pillars: Endpoint/IDE, VCS, CI/CD, Registry, Production."""

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "SITF pillar"

    def technique_count(self):
        return self.techniques.count()

    def __str__(self):
        return self.name


class AttackTechnique(models.Model):
    """An SDLC attack technique, belonging to one pillar."""

    pillar = models.ForeignKey(SITFPillar, on_delete=models.PROTECT, related_name="techniques")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["pillar__order", "name"]
        unique_together = ("pillar", "name")

    def list_findings(self):
        return self.findings.all()

    def __str__(self):
        return f"{self.name} ({self.pillar.name})"


class Project(models.Model):
    """A software project whose code factory is being monitored."""

    name = models.CharField(max_length=120, unique=True)
    repository_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def risk_score(self):
        """Weighted count of open findings: Critical=10, High=5, Medium=2, Low=1."""
        weights = {"CRITICAL": 10, "HIGH": 5, "MEDIUM": 2, "LOW": 1}
        open_findings = self.findings.exclude(status=Finding.Status.RESOLVED)
        return sum(weights[f.severity] for f in open_findings)

    def __str__(self):
        return self.name


class Finding(models.Model):
    """A single security risk found in the SDLC infrastructure."""

    class Severity(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        RESOLVED = "RESOLVED", "Resolved"

    title = models.CharField(max_length=200)
    description = models.TextField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="findings")
    technique = models.ForeignKey(AttackTechnique, on_delete=models.PROTECT, related_name="findings")
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MEDIUM)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reported_findings"
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="owned_findings",
    )
    reported_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-reported_at"]

    @property
    def pillar(self):
        return self.technique.pillar

    def update_status(self, new_status):
        """Change the status and keep resolved_at consistent with it."""
        if new_status not in self.Status.values:
            raise ValueError(f"Unknown status: {new_status}")
        self.status = new_status
        if new_status == self.Status.RESOLVED:
            self.resolved_at = self.resolved_at or timezone.now()
        else:
            self.resolved_at = None
        self.save(update_fields=["status", "resolved_at"])

    def assign_owner(self, user):
        self.assigned_to = user
        self.save(update_fields=["assigned_to"])

    def __str__(self):
        return self.title
