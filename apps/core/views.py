from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import render

from apps.accounts.access import get_allowed_pages
PAGES = {
    "overview": {
        "title": "Overview",
        "icon": "⌂",
        "owner": "PIC 1 - Core Backend",
        "description": "Workspace overview.",
    },
    "my-dashboards": {
        "title": "My Dashboards",
        "icon": "▦",
        "owner": "PIC 4 - Visualization & Dashboard",
        "description": "Manage your dashboards.",
    },
    "data-sources": {
        "title": "Data Sources",
        "icon": "▤",
        "owner": "PIC 2 - Data Connectivity & Extraction",
        "description": "Manage and extract data from multiple sources.",
    },
    "database-connections": {
        "title": "Database Connections",
        "icon": "⇄",
        "owner": "PIC 2 - Data Connectivity & Extraction",
        "description": "Manage external database connections.",
    },
    "database-explorer": {
        "title": "Database Explorer",
        "icon": "⊞",
        "owner": "PIC 2 - Data Connectivity & Extraction",
        "description": "Explore database schemas, tables and columns.",
    },
    "data-manager": {
        "title": "Data Manager",
        "icon": "▧",
        "owner": "PIC 3 - Data Processing & Analytics",
        "description": "Manage, transform and validate internal datasets.",
    },
    "query-builder": {
        "title": "Query Builder",
        "icon": ">_",
        "owner": "PIC 3 - Data Processing & Analytics",
        "description": "Build analytical queries using internal datasets.",
    },
    "visualization-builder": {
        "title": "Visualization Builder",
        "icon": "▥",
        "owner": "PIC 4 - Visualization & Dashboard",
        "description": "Create charts, KPI cards and visual components.",
    },
    "templates": {
        "title": "Templates",
        "icon": "▣",
        "owner": "PIC 4 - Visualization & Dashboard",
        "description": "Explore reusable dashboard templates.",
    },
    "settings": {
        "title": "Settings",
        "icon": "⚙",
        "owner": "PIC 1 - Core Backend",
        "description": "Manage account and application preferences.",
    },
}


def get_page_context(page_key, user):
    if page_key not in PAGES:
        raise Http404("Page not found.")

    allowed_pages = get_allowed_pages(user)

    if page_key not in allowed_pages:
        raise PermissionDenied(
            "You do not have permission to access this page."
        )

    page = PAGES[page_key]

    navigation = [
        {
            "key": key,
            "title": value["title"],
            "icon": value["icon"],
            "url_name": f"core:{key}",
        }
        for key, value in PAGES.items()
        if key in allowed_pages
    ]

    return {
        "navigation": navigation,
        "allowed_pages": allowed_pages,
        "active_page": page_key,
        "page_title": page["title"],
        "page_icon": page["icon"],
        "description": page["description"],
        "owner": page["owner"],
    }


@login_required
def overview(request):

    context = get_page_context(
    "overview",
    request.user,
)

    context["cards"] = [
        {
            "title": "Dashboards",
            "value": "-",
            "description": "Dashboard workspace",
        },
        {
            "title": "Data Sources",
            "value": "-",
            "description": "Available data sources",
        },
        {
            "title": "Datasets",
            "value": "-",
            "description": "Internal datasets",
        },
        {
            "title": "Connections",
            "value": "-",
            "description": "Database connections",
        },
    ]

    return render(request, "core/overview.html", context)


@login_required
def placeholder(request, page):
    context = get_page_context(
        page,
        request.user,
    )

    return render(
        request,
        "core/placeholder.html",
        context,
    )

def permission_denied_view(request, exception):
    allowed_pages = get_allowed_pages(request.user)

    return render(
        request,
        "403.html",
        {
            "can_return_to_overview": "overview" in allowed_pages,
        },
        status=403,
    )