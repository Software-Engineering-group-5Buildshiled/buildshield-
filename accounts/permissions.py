"""Role-based access control: the server checks every request, not just the UI."""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """Allow the view only for logged-in users whose role is in `roles`.

    Superusers are always allowed. Anyone else gets HTTP 403.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if user.is_superuser or user.role in roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("Your role cannot perform this action.")
        return _wrapped
    return decorator
