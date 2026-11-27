from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .access import ROLE_PRIORITY, get_user_role


def role_required(*allowed_roles):
    if not allowed_roles:
        raise ValueError("At least one role is required.")

    invalid_roles = set(allowed_roles) - set(ROLE_PRIORITY)

    if invalid_roles:
        raise ValueError(
            f"Invalid roles: {', '.join(sorted(invalid_roles))}"
        )

    def decorator(view_func):

        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            user_role = get_user_role(request.user)

            if user_role not in allowed_roles:
                raise PermissionDenied(
                    "You do not have permission to access this resource."
                )

            return view_func(request, *args, **kwargs)

        return login_required(wrapped_view)

    return decorator