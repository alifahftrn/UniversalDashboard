from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class UserManagementTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin_group, _ = Group.objects.get_or_create(
            name="Admin"
        )

        cls.editor_group, _ = Group.objects.get_or_create(
            name="Editor"
        )

        cls.viewer_group, _ = Group.objects.get_or_create(
            name="Viewer"
        )

        cls.admin = User.objects.create_user(
            username="admin_test",
            email="admin@example.com",
            password="TestPassword123!",
        )

        cls.admin.groups.add(cls.admin_group)

        cls.editor = User.objects.create_user(
            username="editor_test",
            email="editor@example.com",
            first_name="Data",
            last_name="Analyst",
            password="TestPassword123!",
        )

        cls.editor.groups.add(cls.editor_group)

        cls.viewer = User.objects.create_user(
            username="viewer_test",
            email="viewer@example.com",
            password="TestPassword123!",
        )

        cls.viewer.groups.add(cls.viewer_group)

        cls.inactive_user = User.objects.create_user(
            username="inactive_editor_test",
            password="TestPassword123!",
            is_active=False,
        )

        cls.inactive_user.groups.add(cls.editor_group)

        cls.no_role_user = User.objects.create_user(
            username="no_role_test",
            password="TestPassword123!",
        )

        cls.superuser = User.objects.create_superuser(
            username="superuser_test",
            password="TestPassword123!",
        )

        cls.multi_role_user = User.objects.create_user(
            username="multi_role_test",
            password="TestPassword123!",
        )

        cls.multi_role_user.groups.add(
            cls.editor_group,
            cls.viewer_group,
        )

    def setUp(self):
        self.url = reverse("core:settings")

    def get_usernames(self, response):
        return {
            account.username
            for account in response.context["page_obj"]
        }

    def test_anonymous_user_redirected(self):
        response = self.client.get(self.url)

        login_url = reverse("accounts:login")

        self.assertRedirects(
            response,
            f"{login_url}?next={self.url}",
        )

    def test_admin_can_access_user_management(self):
        self.client.force_login(self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "accounts/user_list.html",
        )

    def test_superuser_can_access_user_management(self):
        self.client.force_login(self.superuser)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_editor_cannot_access_user_management(self):
        self.client.force_login(self.editor)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_viewer_cannot_access_user_management(self):
        self.client.force_login(self.viewer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_user_without_role_cannot_access(self):
        self.client.force_login(self.no_role_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_user_list_displayed(self):
        self.client.force_login(self.admin)

        response = self.client.get(self.url)

        self.assertContains(response, "User Management")

        self.assertEqual(
            self.get_usernames(response),
            {
                "admin_test",
                "editor_test",
                "viewer_test",
                "inactive_editor_test",
                "no_role_test",
                "superuser_test",
                "multi_role_test",
            },
        )

    def test_user_statistics(self):
        self.client.force_login(self.admin)

        response = self.client.get(self.url)

        statistics = response.context["statistics"]

        self.assertEqual(statistics["total"], 7)
        self.assertEqual(statistics["active"], 6)
        self.assertEqual(statistics["inactive"], 1)

    def test_assigned_role_display(self):
        self.client.force_login(self.admin)

        response = self.client.get(self.url)

        roles = {
            account.username: account.assigned_role
            for account in response.context["page_obj"]
        }

        self.assertEqual(
            roles,
            {
                "admin_test": "Admin",
                "editor_test": "Editor",
                "viewer_test": "Viewer",
                "inactive_editor_test": "Editor",
                "no_role_test": "Unassigned",
                "superuser_test": "Admin",
                "multi_role_test": "Editor",
            },
        )

    def test_search_by_username(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            self.url,
            {"q": "viewer_test"},
        )

        self.assertEqual(
            self.get_usernames(response),
            {"viewer_test"},
        )

    def test_search_by_email_and_name(self):
        self.client.force_login(self.admin)

        for keyword in [
            "editor@example.com",
            "Data",
            "Analyst",
        ]:
            with self.subTest(keyword=keyword):
                response = self.client.get(
                    self.url,
                    {"q": keyword},
                )

                self.assertEqual(
                    self.get_usernames(response),
                    {"editor_test"},
                )

    def test_filter_by_role(self):
        self.client.force_login(self.admin)

        expected_roles = {
            "Admin": {
                "admin_test",
                "superuser_test",
            },
            "Editor": {
                "editor_test",
                "inactive_editor_test",
                "multi_role_test",
            },
            "Viewer": {
                "viewer_test",
            },
            "Unassigned": {
                "no_role_test",
            },
        }

        for role, expected_users in expected_roles.items():
            with self.subTest(role=role):
                response = self.client.get(
                    self.url,
                    {"role": role},
                )

                self.assertEqual(
                    self.get_usernames(response),
                    expected_users,
                )

    def test_filter_by_status(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            self.url,
            {"status": "inactive"},
        )

        self.assertEqual(
            self.get_usernames(response),
            {"inactive_editor_test"},
        )

        response = self.client.get(
            self.url,
            {"status": "active"},
        )

        self.assertEqual(
            len(self.get_usernames(response)),
            6,
        )

        self.assertNotIn(
            "inactive_editor_test",
            self.get_usernames(response),
        )

    def test_combined_filters(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            self.url,
            {
                "q": "editor",
                "role": "Editor",
                "status": "active",
            },
        )

        self.assertEqual(
            self.get_usernames(response),
            {"editor_test"},
        )

        self.assertEqual(
            response.context["statistics"]["total"],
            7,
        )

    def test_invalid_filters_are_ignored(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            self.url,
            {
                "role": "InvalidRole",
                "status": "InvalidStatus",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            len(self.get_usernames(response)),
            7,
        )

    def test_search_with_no_results(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            self.url,
            {"q": "unknown_user_xyz"},
        )

        self.assertEqual(
            len(self.get_usernames(response)),
            0,
        )

        self.assertContains(
            response,
            "No users found.",
        )

    def test_pagination(self):
        self.client.force_login(self.admin)

        for index in range(12):
            User.objects.create_user(
                username=f"pagination_user_{index:02d}",
            )

        response = self.client.get(
            self.url,
            {
                "q": "pagination_user",
                "role": "Unassigned",
                "page": 1,
            },
        )

        page_obj = response.context["page_obj"]

        self.assertEqual(len(page_obj.object_list), 10)
        self.assertEqual(page_obj.paginator.count, 12)
        self.assertEqual(page_obj.paginator.num_pages, 2)
        self.assertTrue(page_obj.has_next())

        self.assertContains(response, "page=2")
        self.assertContains(response, "q=pagination_user")
        self.assertContains(response, "role=Unassigned")

        first_page_users = self.get_usernames(response)

        response = self.client.get(
            self.url,
            {
                "q": "pagination_user",
                "role": "Unassigned",
                "page": 2,
            },
        )

        page_obj = response.context["page_obj"]

        self.assertEqual(len(page_obj.object_list), 2)
        self.assertTrue(page_obj.has_previous())
        self.assertFalse(page_obj.has_next())

        second_page_users = self.get_usernames(response)

        self.assertFalse(
            first_page_users & second_page_users
        )

    def test_post_method_not_allowed(self):
        self.client.force_login(self.admin)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 405)