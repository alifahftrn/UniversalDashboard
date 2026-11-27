ROLE_ADMIN = "Admin"
ROLE_EDITOR = "Editor"
ROLE_VIEWER = "Viewer"


ROLE_PRIORITY = (
    ROLE_ADMIN,
    ROLE_EDITOR,
    ROLE_VIEWER,
)


ROLE_PAGES = {
    ROLE_ADMIN: frozenset({
        "overview",
        "my-dashboards",
        "data-sources",
        "database-connections",
        "database-explorer",
        "data-manager",
        "query-builder",
        "visualization-builder",
        "templates",
        "settings",
    }),

    ROLE_EDITOR: frozenset({
        "overview",
        "my-dashboards",
        "data-manager",
        "query-builder",
        "visualization-builder",
        "templates",
    }),

    ROLE_VIEWER: frozenset({
        "overview",
        "my-dashboards",
    }),
}


def get_user_role(user):
    if not user.is_authenticated:
        return None

    if not user.is_active:
        return None

    if user.is_superuser:
        return ROLE_ADMIN

    groups = set(
        user.groups.values_list(
            "name",
            flat=True,
        )
    )

    for role in ROLE_PRIORITY:
        if role in groups:
            return role

    return None


def get_allowed_pages(user):
    role = get_user_role(user)

    return ROLE_PAGES.get(
        role,
        frozenset(),
    )


def can_access_page(user, page_key):
    return page_key in get_allowed_pages(user)