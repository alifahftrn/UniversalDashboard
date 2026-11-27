from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from apps.accounts.access import (
    get_user_role,
    get_allowed_pages,
    can_access_page,
)


User = get_user_model()


class RBACTests(TestCase):

    all_pages = {
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
    }

    editor_pages = {
        "overview",
        "my-dashboards",
        "data-manager",
        "query-builder",
        "visualization-builder",
        "templates",
    }

    viewer_pages = {
        "overview",
        "my-dashboards",
    }

    @classmethod
    def setUpTestData(cls):
        cls.users = {}

        for role in ["Admin", "Editor", "Viewer"]:
            group, _ = Group.objects.get_or_create(
                name=role
            )

            user = User.objects.create_user(
                username=f"{role.lower()}_test",
                password="TestPassword123!",
            )

            user.groups.add(group)

            cls.users[role] = user

        cls.no_role_user = User.objects.create_user(
            username="no_role_test",
            password="TestPassword123!",
        )

        cls.superuser = User.objects.create_superuser(
            username="superuser_test",
            password="TestPassword123!",
        )

    def assert_page_access(self, user, allowed_pages):
        self.client.force_login(user)

        for page in self.all_pages:
            with self.subTest(page=page):
                response = self.client.get(
                    reverse(f"core:{page}")
                )

                expected_status = (
                    200 if page in allowed_pages else 403
                )

                self.assertEqual(
                    response.status_code,
                    expected_status,
                )

    def test_admin_page_access(self):
        self.assert_page_access(
            self.users["Admin"],
            self.all_pages,
        )

    def test_editor_page_access(self):
        self.assert_page_access(
            self.users["Editor"],
            self.editor_pages,
        )

    def test_viewer_page_access(self):
        self.assert_page_access(
            self.users["Viewer"],
            self.viewer_pages,
        )

    def test_superuser_page_access(self):
        self.assert_page_access(
            self.superuser,
            self.all_pages,
        )

    def test_user_without_role_is_denied(self):
        self.assert_page_access(
            self.no_role_user,
            set(),
        )

    def test_role_detection(self):
        for role, user in self.users.items():
            with self.subTest(role=role):
                self.assertEqual(
                    get_user_role(user),
                    role,
                )

    def test_superuser_role(self):
        self.assertEqual(
            get_user_role(self.superuser),
            "Admin",
        )

    def test_allowed_pages(self):
        self.assertEqual(
            get_allowed_pages(self.users["Admin"]),
            self.all_pages,
        )

        self.assertEqual(
            get_allowed_pages(self.users["Editor"]),
            self.editor_pages,
        )

        self.assertEqual(
            get_allowed_pages(self.users["Viewer"]),
            self.viewer_pages,
        )

    def test_page_permission(self):
        viewer = self.users["Viewer"]

        self.assertTrue(
            can_access_page(viewer, "overview")
        )

        self.assertFalse(
            can_access_page(viewer, "database-connections")
        )

    def test_role_priority(self):
        viewer = self.users["Viewer"]

        viewer.groups.add(
            Group.objects.get(name="Editor")
        )

        self.assertEqual(
            get_user_role(viewer),
            "Editor",
        )

    def test_navigation_visibility(self):
        role_pages = {
            "Admin": self.all_pages,
            "Editor": self.editor_pages,
            "Viewer": self.viewer_pages,
        }

        for role, expected_pages in role_pages.items():
            with self.subTest(role=role):
                self.client.force_login(
                    self.users[role]
                )

                response = self.client.get(
                    reverse("core:overview")
                )

                navigation = response.context["navigation"]

                actual_pages = {
                    item["key"] for item in navigation
                }

                self.assertEqual(
                    actual_pages,
                    expected_pages,
                )

    def test_custom_forbidden_page(self):
        self.client.force_login(
            self.users["Viewer"]
        )

        response = self.client.get(
            reverse("core:database-connections")
        )

        self.assertEqual(response.status_code, 403)

        self.assertTemplateUsed(
            response,
            "403.html",
        )

        self.assertContains(
            response,
            "Access Denied",
            status_code=403,
        )

    def test_no_role_user_cannot_return_to_overview(self):
        self.client.force_login(
            self.no_role_user
        )

        response = self.client.get(
            reverse("core:overview")
        )

        self.assertEqual(response.status_code, 403)

        self.assertFalse(
            response.context["can_return_to_overview"]
        )

    def test_inactive_user_has_no_access(self):
        user = self.users["Admin"]
        user.is_active = False

        self.assertIsNone(
            get_user_role(user)
        )

        self.assertEqual(
            get_allowed_pages(user),
            frozenset(),
        )

    def test_viewer_cannot_see_restricted_shortcuts(self):
        self.client.force_login(
            self.users["Viewer"]
        )

        response = self.client.get(
            reverse("core:overview")
        )

        self.assertNotContains(
            response,
            "Connect Data",
        )

        self.assertNotContains(
            response,
            "Transform Data",
        )

        self.assertNotContains(
            response,
            "Build Visualization",
        )