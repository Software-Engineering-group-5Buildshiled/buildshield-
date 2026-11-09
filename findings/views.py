import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.permissions import role_required

from .dashboard import Dashboard
from .forms import AssignForm, DashboardFilterForm, FindingForm, ProjectForm, StatusForm
from .models import Finding, Project, SITFPillar

DEV = User.Role.DEVELOPER
ANALYST = User.Role.ANALYST
ADMIN = User.Role.ADMIN


def _filtered_project(request):
    """Read ?project= safely: invalid values are ignored, never trusted."""
    form = DashboardFilterForm(request.GET or None)
    project = form.cleaned_data["project"] if form.is_valid() else None
    return form, project


@login_required
def dashboard(request):
    form, project = _filtered_project(request)
    board = Dashboard(project=project)
    context = {
        "filter_form": form,
        "project": project,
        "totals": board.totals(),
        "stat_cards": board.stat_cards(),
        "period": board.trend_period(),
        "recent": board.recent_open(),
        "chart_pillar": board.chart_by_pillar(),
        "chart_severity": board.chart_by_severity(),
        "chart_trend": board.chart_status_trend(),
    }
    return render(request, "findings/dashboard.html", context)


@login_required
def finding_list(request):
    findings = Finding.objects.select_related("project", "technique__pillar", "assigned_to")
    # Only accept filter values that are real choices.
    status = request.GET.get("status")
    severity = request.GET.get("severity")
    pillar = request.GET.get("pillar")
    query = request.GET.get("q", "").strip()[:100]
    if query:
        findings = findings.filter(
            Q(title__icontains=query) | Q(project__name__icontains=query)
            | Q(technique__name__icontains=query) | Q(technique__pillar__name__icontains=query)
        )
    if status in Finding.Status.values:
        findings = findings.filter(status=status)
    if severity in Finding.Severity.values:
        findings = findings.filter(severity=severity)
    if pillar and pillar.isdigit():
        findings = findings.filter(technique__pillar_id=int(pillar))
    context = {
        "findings": findings,
        "statuses": Finding.Status.choices,
        "severities": Finding.Severity.choices,
        "pillars": SITFPillar.objects.all(),
        "current": {"status": status, "severity": severity, "pillar": pillar, "q": query},
    }
    return render(request, "findings/finding_list.html", context)


@role_required(DEV, ANALYST)
def finding_create(request):
    form = FindingForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        finding = form.save(commit=False)
        finding.reported_by = request.user  # set by the server, never by the form
        finding.save()
        messages.success(request, "Finding reported.")
        return redirect("finding_detail", pk=finding.pk)
    return render(request, "findings/finding_form.html", {"form": form})


@login_required
def finding_detail(request, pk):
    finding = get_object_or_404(
        Finding.objects.select_related("project", "technique__pillar", "reported_by", "assigned_to"),
        pk=pk,
    )
    context = {
        "finding": finding,
        "status_form": StatusForm(initial={"status": finding.status}),
        "assign_form": AssignForm(initial={"assigned_to": finding.assigned_to}),
        "can_update": can_update_status(request.user, finding),
    }
    return render(request, "findings/finding_detail.html", context)


def can_update_status(user, finding):
    """Analysts may update any finding; developers only their own or assigned ones."""
    if user.is_superuser or user.role == ANALYST:
        return True
    if user.role == DEV:
        return finding.reported_by_id == user.id or finding.assigned_to_id == user.id
    return False


@require_POST
@role_required(DEV, ANALYST)
def finding_update_status(request, pk):
    finding = get_object_or_404(Finding, pk=pk)
    if not can_update_status(request.user, finding):
        raise PermissionDenied("You can only update findings you reported or own.")
    form = StatusForm(request.POST)
    if form.is_valid():
        finding.update_status(form.cleaned_data["status"])
        messages.success(request, f"Status changed to {finding.get_status_display()}.")
    else:
        messages.error(request, "Choose a valid status.")
    return redirect("finding_detail", pk=pk)


@require_POST
@role_required(ANALYST)
def finding_assign(request, pk):
    finding = get_object_or_404(Finding, pk=pk)
    form = AssignForm(request.POST)
    if form.is_valid():
        finding.assign_owner(form.cleaned_data["assigned_to"])
        messages.success(request, f"Assigned to {finding.assigned_to.username}.")
    else:
        messages.error(request, "Choose an active developer or analyst.")
    return redirect("finding_detail", pk=pk)


@role_required(ANALYST)
def summary_report(request):
    form, project = _filtered_project(request)
    board = Dashboard(project=project)
    if request.GET.get("format") == "csv":
        return _csv_response(board.summary_report(), project)
    context = {"filter_form": form, "project": project, "rows": board.summary_report()}
    return render(request, "findings/summary_report.html", context)


def _safe_cell(value):
    """Stop CSV/formula injection when the file is opened in Excel."""
    text = str(value)
    if text and text[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + text
    return text


def _csv_response(rows, project):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="factoryguard-summary.csv"'
    writer = csv.writer(response)
    writer.writerow(["Project", _safe_cell(project.name) if project else "All projects"])
    writer.writerow(["Pillar", "Total", "Open", "Critical", "Resolved"])
    for row in rows:
        writer.writerow([_safe_cell(row["pillar"]), row["total"], row["open"], row["critical"], row["resolved"]])
    return response


@role_required(ADMIN)
def project_list(request):
    form = ProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project added.")
        return redirect("project_list")
    projects = Project.objects.all()
    return render(request, "findings/project_list.html", {"form": form, "projects": projects})
