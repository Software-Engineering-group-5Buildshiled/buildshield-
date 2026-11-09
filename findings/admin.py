from django.contrib import admin

from .models import AttackTechnique, Finding, Project, SITFPillar


@admin.register(SITFPillar)
class SITFPillarAdmin(admin.ModelAdmin):
    list_display = ("name", "order")


@admin.register(AttackTechnique)
class AttackTechniqueAdmin(admin.ModelAdmin):
    list_display = ("name", "pillar")
    list_filter = ("pillar",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "repository_url", "created_at")


@admin.register(Finding)
class FindingAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "technique", "severity", "status", "assigned_to")
    list_filter = ("severity", "status", "project")
    search_fields = ("title", "description")
