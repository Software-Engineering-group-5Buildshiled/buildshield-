"""Forms validate every input on the server before it reaches the database."""
from django import forms
from django.contrib.auth import get_user_model

from .models import Finding, Project

User = get_user_model()


class FindingForm(forms.ModelForm):
    class Meta:
        model = Finding
        fields = ["title", "project", "technique", "severity", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}
        help_texts = {
            "technique": "The SITF attack technique; its pillar is set from it.",
        }

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if len(title) < 5:
            raise forms.ValidationError("Use at least 5 characters so others know what the risk is.")
        return title

    def clean_description(self):
        description = self.cleaned_data["description"].strip()
        if len(description) > 5000:
            raise forms.ValidationError("Keep the description under 5,000 characters.")
        return description


class StatusForm(forms.Form):
    status = forms.ChoiceField(choices=Finding.Status.choices)


class AssignForm(forms.Form):
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(
            is_active=True, role__in=[User.Role.DEVELOPER, User.Role.ANALYST]
        ).order_by("username"),
        label="Owner",
    )


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "repository_url"]

    def clean_repository_url(self):
        url = self.cleaned_data["repository_url"]
        if url and not url.startswith("https://"):
            raise forms.ValidationError("Use an https:// link.")
        return url


class DashboardFilterForm(forms.Form):
    project = forms.ModelChoiceField(
        queryset=Project.objects.all(), required=False, empty_label="All projects"
    )
