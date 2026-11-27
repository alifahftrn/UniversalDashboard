from django.urls import path

from . import views


app_name = "core"


urlpatterns = [
    path("", views.overview, name="overview"),

    path(
        "dashboards/",
        views.placeholder,
        {"page": "my-dashboards"},
        name="my-dashboards",
    ),

    path(
        "data-sources/",
        views.placeholder,
        {"page": "data-sources"},
        name="data-sources",
    ),

    path(
        "connections/",
        views.placeholder,
        {"page": "database-connections"},
        name="database-connections",
    ),

    path(
        "explorer/",
        views.placeholder,
        {"page": "database-explorer"},
        name="database-explorer",
    ),

    path(
        "data-manager/",
        views.placeholder,
        {"page": "data-manager"},
        name="data-manager",
    ),

    path(
        "query/",
        views.placeholder,
        {"page": "query-builder"},
        name="query-builder",
    ),

    path(
        "visualize/",
        views.placeholder,
        {"page": "visualization-builder"},
        name="visualization-builder",
    ),

    path(
        "templates/",
        views.placeholder,
        {"page": "templates"},
        name="templates",
    ),

    path(
        "settings/",
        views.placeholder,
        {"page": "settings"},
        name="settings",
    ),
]