from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.db.models import (
    Case,
    CharField,
    Count,
    Exists,
    OuterRef,
    Q,
    Value,
    When,
)
from django.shortcuts import render
from django.views.decorators.http import require_safe

from apps.accounts.access import ROLE_PRIORITY
from apps.accounts.decorators import role_required
from apps.core.views import get_page_context


User = get_user_model()


def get_user_queryset():
    role_conditions = [
        When(
            is_superuser=True,
            then=Value("Admin"),
        )
    ]

    for role in ROLE_PRIORITY:
        role_conditions.append(
            When(
                Exists(
                    Group.objects.filter(
                        user=OuterRef("pk"),
                        name=role,
                    )
                ),
                then=Value(role),
            )
        )

    return User.objects.annotate(
        assigned_role=Case(
            *role_conditions,
            default=Value("Unassigned"),
            output_field=CharField(),
        )
    )


@role_required("Admin")
@require_safe
def user_list(request):
    search = request.GET.get("q", "").strip()[:150]
    role_filter = request.GET.get("role", "")
    status_filter = request.GET.get("status", "")

    if role_filter not in (*ROLE_PRIORITY, "Unassigned"):
        role_filter = ""

    if status_filter not in ("active", "inactive"):
        status_filter = ""

    users = get_user_queryset()

    statistics = User.objects.aggregate(
        total=Count("pk"),
        active=Count(
            "pk",
            filter=Q(is_active=True),
        ),
        inactive=Count(
            "pk",
            filter=Q(is_active=False),
        ),
    )

    if search:
        users = users.filter(
            Q(username__icontains=search)
            | Q(email__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
        )

    if role_filter:
        users = users.filter(
            assigned_role=role_filter
        )

    if status_filter == "active":
        users = users.filter(is_active=True)

    elif status_filter == "inactive":
        users = users.filter(is_active=False)

    users = users.order_by("username", "pk")

    paginator = Paginator(users, 10)

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    context = get_page_context(
        "settings",
        request.user,
    )

    context.update(
        {
            "page_title": "User Management",
            "page_obj": page_obj,
            "statistics": statistics,
            "search": search,
            "role_filter": role_filter,
            "status_filter": status_filter,
            "role_choices": (
                *ROLE_PRIORITY,
                "Unassigned",
            ),
        }
    )

    return render(
        request,
        "accounts/user_list.html",
        context,
    )