"""Unit tests for FactoryGuard.

TC-01 and TC-02 are the two test cases documented in the Part 2 test plan.
The others add extra coverage and run in the same CI pipeline.
"""
from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .dashboard import Dashboard
from .forms import FindingForm
from .models import AttackTechnique, Finding, Project, SITFPillar
from .views import _safe_cell


class FactoryGuardTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pillar = SITFPillar.objects.create(name="CI/CD", order=3)
        cls.technique = AttackTechnique.objects.create(pillar=cls.pillar, name="Action Cache Poisoning")
        cls.project = Project.objects.create(name="Payments API")
        cls.dev = User.objects.create_user("dev1", password="x-Strong-Pass-1", role=User.Role.DEVELOPER)
        cls.other_dev = User.objects.create_user("dev2", password="x-Strong-Pass-2", role=User.Role.DEVELOPER)
        cls.analyst = User.objects.create_user("analyst1", password="x-Strong-Pass-3", role=User.Role.ANALYST)

    def make_finding(self, **kwargs):
        defaults = dict(
            title="Build cache can be poisoned",
            description="Shared cache key across forks.",
            project=self.project,
            technique=self.technique,
            severity=Finding.Severity.HIGH,
            reported_by=self.dev,
        )
        defaults.update(kwargs)
        return Finding.objects.create(**defaults)


class TC01FindingStatusTests(FactoryGuardTestBase):
    """TC-01: Resolving a finding records when it was resolved; reopening clears it."""

    def test_resolving_sets_resolved_at(self):
        finding = self.make_finding()
        self.assertIsNone(finding.resolved_at)

        finding.update_status(Finding.Status.RESOLVED)
        finding.refresh_from_db()

        self.assertEqual(finding.status, Finding.Status.RESOLVED)
        self.assertIsNotNone(finding.resolved_at)

    def test_reopening_clears_resolved_at(self):
        finding = self.make_finding()
        finding.update_status(Finding.Status.RESOLVED)
        finding.update_status(Finding.Status.OPEN)
        finding.refresh_from_db()

        self.assertEqual(finding.status, Finding.Status.OPEN)
        self.assertIsNone(finding.resolved_at)

    def test_invalid_status_is_rejected(self):
        finding = self.make_finding()
        with self.assertRaises(ValueError):
            finding.update_status("DELETED")


class TC02AccessControlTests(FactoryGuardTestBase):
    """TC-02: The server blocks actions a user's role does not allow."""

    def test_developer_cannot_assign_owner(self):
        finding = self.make_finding()
        self.client.login(username="dev1", password="x-Strong-Pass-1")

        response = self.client.post(
            reverse("finding_assign", args=[finding.pk]), {"assigned_to": self.dev.pk}
        )

        self.assertEqual(response.status_code, 403)
        finding.refresh_from_db()
        self.assertIsNone(finding.assigned_to)

    def test_developer_cannot_update_someone_elses_finding(self):
        finding = self.make_finding()  # reported by dev1, not assigned to dev2
        self.client.login(username="dev2", password="x-Strong-Pass-2")

        response = self.client.post(
            reverse("finding_update_status", args=[finding.pk]), {"status": Finding.Status.RESOLVED}
        )

        self.assertEqual(response.status_code, 403)
        finding.refresh_from_db()
        self.assertEqual(finding.status, Finding.Status.OPEN)

    def test_analyst_can_assign_owner(self):
        finding = self.make_finding()
        self.client.login(username="analyst1", password="x-Strong-Pass-3")

        self.client.post(reverse("finding_assign", args=[finding.pk]), {"assigned_to": self.dev.pk})

        finding.refresh_from_db()
        self.assertEqual(finding.assigned_to, self.dev)


class ExtraTests(FactoryGuardTestBase):
    def test_anonymous_user_is_sent_to_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_form_rejects_very_short_title(self):
        form = FindingForm(data={
            "title": "abc", "project": self.project.pk, "technique": self.technique.pk,
            "severity": "HIGH", "description": "x",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_reporter_is_set_by_server_not_form(self):
        self.client.login(username="dev1", password="x-Strong-Pass-1")
        self.client.post(reverse("finding_create"), {
            "title": "Secrets in build logs", "project": self.project.pk,
            "technique": self.technique.pk, "severity": "CRITICAL",
            "description": "Token printed by a debug step.", "reported_by": self.analyst.pk,
        })
        finding = Finding.objects.get(title="Secrets in build logs")
        self.assertEqual(finding.reported_by, self.dev)

    def test_dashboard_renders_charts(self):
        self.make_finding()
        self.client.login(username="analyst1", password="x-Strong-Pass-3")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data:image/png;base64,", count=3)

    def test_dashboard_loads_with_no_findings(self):
        self.client.login(username="analyst1", password="x-Strong-Pass-3")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data:image/png;base64,", count=3)

    def test_dashboard_ignores_invalid_project_filter(self):
        self.client.login(username="analyst1", password="x-Strong-Pass-3")
        for bad in ["99999", "abc", "1 OR 1=1"]:
            response = self.client.get(reverse("dashboard"), {"project": bad})
            self.assertEqual(response.status_code, 200)
            self.assertIsNone(response.context["project"])

    def test_totals_counts_findings(self):
        self.make_finding(severity=Finding.Severity.CRITICAL)
        self.make_finding(severity=Finding.Severity.CRITICAL, status=Finding.Status.IN_PROGRESS)
        self.make_finding(severity=Finding.Severity.LOW)
        self.make_finding(severity=Finding.Severity.CRITICAL).update_status(Finding.Status.RESOLVED)
        self.make_finding(severity=Finding.Severity.HIGH).update_status(Finding.Status.RESOLVED)
        # A finding in another project must not count when filtering by project.
        other = Project.objects.create(name="Mobile App")
        self.make_finding(project=other)

        totals = Dashboard(project=self.project).totals()

        self.assertEqual(totals, {"total": 5, "open": 3, "critical_open": 2, "resolved": 2})
        self.assertEqual(Dashboard().totals()["total"], 6)

    def test_csv_cells_cannot_start_a_formula(self):
        self.assertEqual(_safe_cell("=HYPERLINK(1)"), "'=HYPERLINK(1)")
        self.assertEqual(_safe_cell("CI/CD"), "CI/CD")

    def test_risk_score_ignores_resolved_findings(self):
        self.make_finding(severity=Finding.Severity.CRITICAL)
        resolved = self.make_finding(severity=Finding.Severity.HIGH)
        resolved.update_status(Finding.Status.RESOLVED)
        self.assertEqual(self.project.risk_score(), 10)
