"""Dashboard service: turns findings into Matplotlib charts.

Charts are rendered in memory as PNG and embedded as base64, so no files are
written to disk and no user input is ever used as a file path.
"""
import base64
import io
from datetime import timedelta

import matplotlib

matplotlib.use("Agg")  # server-side rendering, no display needed
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.legend_handler import HandlerTuple  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from django.db.models import Count, Q  # noqa: E402
from django.utils import timezone  # noqa: E402

from .models import Finding, SITFPillar  # noqa: E402

INK = "#0E1726"
MUTED = "#5B6676"
GRID = "#E8ECF1"
SEVERITY_COLOURS = {
    "LOW": "#3E7C59",
    "MEDIUM": "#C9932B",
    "HIGH": "#D2642A",
    "CRITICAL": "#A8322D",
}
OPEN_COLOUR = "#2F6FD6"
RESOLVED_COLOUR = "#D5DBE3"
TREND_FILL = "#E3ECFA"  # flat fill under the trend line (no gradients)


def _style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9, length=0, pad=6)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _label(ax, x=None, y=None):
    if x:
        ax.set_xlabel(x, color=MUTED, fontsize=9, labelpad=8)
    if y:
        ax.set_ylabel(y, color=MUTED, fontsize=9, labelpad=8)


def _to_base64(fig):
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=144, bbox_inches="tight", facecolor="white")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _sparkline(values, width=120, height=44, pad=5):
    """Smooth SVG path for a small trend line, plus the filled area and end point.

    Built from numbers only (never user input). Uses Catmull-Rom curves so the
    line bends smoothly through every weekly value.
    """
    if not values:
        return None
    low, high = min(values), max(values)
    span = (high - low) or 1
    step = (width - pad) / max(len(values) - 1, 1)
    pts = [(i * step, height - pad - (v - low) / span * (height - 2 * pad)) for i, v in enumerate(values)]
    line = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(len(pts) - 1):
        p0, p1, p2 = pts[max(i - 1, 0)], pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        line += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    end_x, end_y = pts[-1]
    area = f"{line} L{end_x:.1f},{height} L{pts[0][0]:.1f},{height} Z"
    return {"line": line, "area": area, "x": f"{end_x:.1f}", "y": f"{end_y:.1f}",
            "viewbox": f"-2 -2 {width + 4} {height + 4}"}


class Dashboard:
    def __init__(self, project=None):
        self.filters = {"project": project}
        self.findings = Finding.objects.select_related("technique__pillar")
        if project is not None:
            self.findings = self.findings.filter(project=project)

    # --- numbers for the summary strip ----------------------------------
    def totals(self):
        return self.findings.aggregate(
            total=Count("id"),
            open=Count("id", filter=~Q(status=Finding.Status.RESOLVED)),
            critical_open=Count(
                "id",
                filter=Q(severity=Finding.Severity.CRITICAL) & ~Q(status=Finding.Status.RESOLVED),
            ),
            resolved=Count("id", filter=Q(status=Finding.Status.RESOLVED)),
        )

    def _week_points(self, weeks=8):
        now = timezone.now()
        return [now - timedelta(weeks=w) for w in range(weeks - 1, -1, -1)]

    def trend_period(self, weeks=8):
        """First and last dates covered by the weekly trend."""
        points = self._week_points(weeks)
        return {"start": points[0], "end": points[-1]}

    def weekly_series(self, weeks=8):
        """For each week-end point: findings reported, resolved and still open by then."""
        series = {"total": [], "resolved": [], "open": [], "critical_open": []}
        critical = self.findings.filter(severity=Finding.Severity.CRITICAL)
        for point in self._week_points(weeks):
            reported = self.findings.filter(reported_at__lte=point).count()
            resolved = self.findings.filter(resolved_at__lte=point).count()
            crit_reported = critical.filter(reported_at__lte=point).count()
            crit_resolved = critical.filter(resolved_at__lte=point).count()
            series["total"].append(reported)
            series["resolved"].append(resolved)
            series["open"].append(reported - resolved)
            series["critical_open"].append(crit_reported - crit_resolved)
        return series

    def stat_cards(self):
        """The four summary cards: value, week-on-week change and a sparkline."""
        totals = self.totals()
        series = self.weekly_series()
        cards = [
            # key, label, icon, whether a rise is good news
            ("open", "Open findings", "search", False),
            ("critical_open", "Critical and open", "alert", False),
            ("resolved", "Resolved", "check", True),
            ("total", "Reported in total", "box", None),
        ]
        result = []
        for key, label, icon, rise_is_good in cards:
            values = series[key]
            previous, latest = values[-2], values[-1]
            diff = latest - previous
            # Percentage change from last week; None when last week was zero.
            change = round(abs(diff) / previous * 100) if previous else None
            if diff == 0 or rise_is_good is None:
                tone = "neutral"
            else:
                tone = "good" if (diff > 0) == rise_is_good else "bad"
            result.append({
                "key": key, "label": label, "icon": icon, "value": totals[key],
                "change": change,
                "direction": "up" if diff > 0 else "down" if diff < 0 else "flat",
                "tone": tone, "spark": _sparkline(values),
            })
        return result

    def recent_open(self, limit=5):
        return (
            self.findings.exclude(status=Finding.Status.RESOLVED)
            .select_related("project", "technique__pillar")
            .order_by("-reported_at")[:limit]
        )

    # --- charts -----------------------------------------------------------
    def chart_by_pillar(self):
        """Open findings per SITF pillar, stacked by severity."""
        pillars = list(SITFPillar.objects.all())
        names = [p.name for p in pillars]
        open_findings = self.findings.exclude(status=Finding.Status.RESOLVED)
        fig = Figure(figsize=(7.4, 3.6))
        ax = fig.subplots()
        left = [0] * len(pillars)
        for severity, label in Finding.Severity.choices:
            counts = [
                open_findings.filter(technique__pillar=p, severity=severity).count() for p in pillars
            ]
            # Only label severities that actually appear, so the legend matches the bars.
            ax.barh(names, counts, left=left, color=SEVERITY_COLOURS[severity],
                    label=label if any(counts) else None, height=0.5)
            left = [a + b for a, b in zip(left, counts)]
        # Total at the end of each bar.
        for y, total in enumerate(left):
            ax.text(total + max(max(left), 1) * 0.015, y, str(total), va="center",
                    color=INK, fontsize=9, fontweight="bold")
        ax.invert_yaxis()
        _style(ax)
        ax.yaxis.grid(False)
        ax.xaxis.grid(True, color=GRID, linewidth=0.8)
        ax.spines["left"].set_visible(False)
        ax.set_xlim(0, max(max(left), 1) * 1.1)
        ax.xaxis.get_major_locator().set_params(integer=True)
        ax.tick_params(axis="y", labelsize=10, colors=INK)
        _label(ax, x="Open findings", y="SITF pillar")
        if any(left):
            ax.legend(frameon=False, fontsize=9, ncol=4, loc="lower center", bbox_to_anchor=(0.5, 1.0),
                      handlelength=1.4, handleheight=0.9, columnspacing=1.6, labelcolor=MUTED)
        return _to_base64(fig)

    def chart_by_severity(self):
        """All findings by severity, split open vs resolved."""
        labels = [label for _, label in Finding.Severity.choices]
        keys = [key for key, _ in Finding.Severity.choices]
        open_counts = [
            self.findings.filter(severity=k).exclude(status=Finding.Status.RESOLVED).count() for k in keys
        ]
        resolved_counts = [
            self.findings.filter(severity=k, status=Finding.Status.RESOLVED).count() for k in keys
        ]
        fig = Figure(figsize=(4.6, 3.6))
        ax = fig.subplots()
        ax.bar(labels, open_counts, color=[SEVERITY_COLOURS[k] for k in keys], width=0.5)
        ax.bar(labels, resolved_counts, bottom=open_counts, color=RESOLVED_COLOUR, width=0.5)
        _style(ax)
        ax.spines["left"].set_visible(False)
        ax.yaxis.get_major_locator().set_params(integer=True)
        _label(ax, x="Severity", y="Findings")
        # Coloured part = open (colour shows severity); grey part = resolved.
        # The "Open" legend entry shows all four severity colours so it matches the bars.
        open_handle = tuple(Patch(color=SEVERITY_COLOURS[k]) for k in keys)
        ax.legend(handles=[open_handle, Patch(color=RESOLVED_COLOUR)], labels=["Open", "Resolved"],
                  handler_map={tuple: HandlerTuple(ndivide=None, pad=0)},
                  frameon=False, fontsize=9, ncol=2, loc="lower right", bbox_to_anchor=(1, 1.0),
                  labelcolor=MUTED)
        return _to_base64(fig)

    def chart_status_trend(self, weeks=8):
        """Findings still open at the end of each of the last `weeks` weeks."""
        points = self._week_points(weeks)
        open_counts = self.weekly_series(weeks)["open"]
        labels = [p.strftime("%d %b") for p in points]
        fig = Figure(figsize=(7, 3.0))
        ax = fig.subplots()
        ax.fill_between(labels, open_counts, color=TREND_FILL)
        ax.plot(labels, open_counts, color=OPEN_COLOUR, linewidth=2.2, marker="o", markersize=6,
                markerfacecolor="white", markeredgewidth=2)
        _style(ax)
        ax.xaxis.grid(True, color=GRID, linewidth=0.8)
        ax.spines["left"].set_visible(False)
        ax.set_ylim(bottom=0, top=max(max(open_counts), 1) * 1.15)
        ax.margins(x=0.03)
        ax.yaxis.get_major_locator().set_params(integer=True)
        _label(ax, x="Week ending", y="Open findings")
        return _to_base64(fig)

    def summary_report(self):
        """Rows for the summary report: one per pillar."""
        rows = []
        for pillar in SITFPillar.objects.all():
            qs = self.findings.filter(technique__pillar=pillar)
            rows.append({
                "pillar": pillar.name,
                "total": qs.count(),
                "open": qs.exclude(status=Finding.Status.RESOLVED).count(),
                "critical": qs.filter(severity=Finding.Severity.CRITICAL).count(),
                "resolved": qs.filter(status=Finding.Status.RESOLVED).count(),
            })
        return rows
