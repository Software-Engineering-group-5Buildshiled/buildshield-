"""Load the five SITF pillars and example techniques.

    python manage.py seed_sitf          # pillars and techniques only
    python manage.py seed_sitf --demo   # also demo users, projects and findings

Action Cache Poisoning and Imposter Commits come from the project brief. The
other techniques are illustrative examples; check the official SITF catalogue
(https://wiz-sec-public.github.io/SITF/) and replace them with its exact names.
"""
import random
import secrets
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from findings.models import AttackTechnique, Finding, Project, SITFPillar

PILLARS = [
    ("Endpoint/IDE", "Developer machines, IDEs and their extensions.",
     ["Malicious IDE extension", "Compromised developer workstation"]),
    ("VCS", "Version control systems such as GitHub.",
     ["Imposter Commits", "Branch protection bypass"]),
    ("CI/CD", "Build pipelines and runners.",
     ["Action Cache Poisoning", "Secrets exposed in build logs"]),
    ("Registry", "Package and container registries.",
     ["Dependency confusion", "Typosquatted package"]),
    ("Production", "Where built software is deployed and runs.",
     ["Compromised deploy credentials", "Unsigned artifact deployed"]),
]


class Command(BaseCommand):
    help = "Load SITF pillars and techniques, optionally with demo data."

    def add_arguments(self, parser):
        parser.add_argument("--demo", action="store_true", help="Also create demo users and findings.")

    @transaction.atomic
    def handle(self, *args, **options):
        for order, (name, description, techniques) in enumerate(PILLARS, start=1):
            pillar, _ = SITFPillar.objects.update_or_create(
                name=name, defaults={"description": description, "order": order}
            )
            for technique in techniques:
                AttackTechnique.objects.get_or_create(pillar=pillar, name=technique)
        self.stdout.write(self.style.SUCCESS("Loaded 5 SITF pillars and their techniques."))

        if options["demo"]:
            self._demo()

    def _demo(self):
        users = {}
        for username, role in [("dev1", User.Role.DEVELOPER), ("analyst1", User.Role.ANALYST),
                               ("admin1", User.Role.ADMIN)]:
            user, created = User.objects.get_or_create(username=username, defaults={"role": role})
            if created:
                # A random password per demo user; never a hard-coded one.
                password = secrets.token_urlsafe(12)
                user.set_password(password)
                user.is_staff = role == User.Role.ADMIN
                user.save()
                self.stdout.write(f"  {username} ({user.get_role_display()}) password: {password}")
            users[username] = user

        projects = [
            Project.objects.get_or_create(name=name, defaults={"repository_url": url})[0]
            for name, url in [("Payments API", "https://github.com/example/payments-api"),
                              ("Mobile App", "https://github.com/example/mobile-app")]
        ]
        if Finding.objects.exists():
            self.stdout.write("Findings already exist; skipping demo findings.")
            return

        rng = random.Random(42)  # fixed seed: the same demo data every time
        techniques = list(AttackTechnique.objects.all())
        severities = Finding.Severity.values
        now = timezone.now()
        for i in range(40):
            reported = now - timedelta(days=rng.randint(0, 55))
            finding = Finding.objects.create(
                title=f"Demo finding {i + 1}",
                description="Generated demo data.",
                project=rng.choice(projects),
                technique=rng.choice(techniques),
                severity=rng.choices(severities, weights=[3, 4, 3, 1])[0],
                reported_by=users["dev1"],
                assigned_to=rng.choice([users["dev1"], users["analyst1"], None]),
                reported_at=reported,
            )
            if rng.random() < 0.45:
                finding.status = Finding.Status.RESOLVED
                finding.resolved_at = min(now, reported + timedelta(days=rng.randint(1, 14)))
                finding.save()
            elif rng.random() < 0.4:
                finding.status = Finding.Status.IN_PROGRESS
                finding.save()
        self.stdout.write(self.style.SUCCESS("Created 2 demo projects and 40 demo findings."))
