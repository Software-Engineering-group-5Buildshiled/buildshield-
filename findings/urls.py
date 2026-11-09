from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("findings/", views.finding_list, name="finding_list"),
    path("findings/new/", views.finding_create, name="finding_create"),
    path("findings/<int:pk>/", views.finding_detail, name="finding_detail"),
    path("findings/<int:pk>/status/", views.finding_update_status, name="finding_update_status"),
    path("findings/<int:pk>/assign/", views.finding_assign, name="finding_assign"),
    path("report/", views.summary_report, name="summary_report"),
    path("projects/", views.project_list, name="project_list"),
]
