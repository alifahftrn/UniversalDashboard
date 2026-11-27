from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from apps.accounts.decorators import role_required


User = get_user_model()


@role_required("Admin")
def admin_view(request):
    return HttpResponse("Admin Access")


@role_required("Admin", "Editor")
def editor_view(request):
    return HttpResponse("Editor Access")


@role_required("Admin", "Editor", "Viewer")
def dashboard_view(request):
    return HttpResponse("Dashboard Access")


class AuthorizationDecoratorTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.users = {}

        for role in ["Admin", "Editor", "Viewer"]:
            group, _ = Group.objects.get_or_create(
                name=role
            )

            user = User.objects.create_user(
                username=f"{role.lower()}_decorator_test",
                password="TestPassword123!",
            )

            user.groups.add(group)

            cls.users[role] = user

        cls.no_role_user = User.objects.create_user(
            username="no_role_decorator_test",
            password="TestPassword123!",
        )

        cls.superuser = User.objects.create_superuser(
            username="superuser_decorator_test",
            password="TestPassword123!",
        )

    def setUp(self):
        self.factory = RequestFactory()

    def build_request(self, user):
        request = self.factory.get("/")
        request.user = user

        return request

    def test_anonymous_user_redirected(self):
        request = self.build_request(
            AnonymousUser()
        )

        response = admin_view(request)

        self.assertEqual(response.status_code, 302)

        self.assertEqual(
            response.url,
            "/accounts/login/?next=/",
        )

    def test_admin_access_allowed(self):
        request = self.build_request(
            self.users["Admin"]
        )

        response = admin_view(request)

        self.assertEqual(response.status_code, 200)

    def test_editor_denied_admin_access(self):
        request = self.build_request(
            self.users["Editor"]
        )

        with self.assertRaises(PermissionDenied):
            admin_view(request)

    def test_viewer_denied_admin_access(self):
        request = self.build_request(
            self.users["Viewer"]
        )

        with self.assertRaises(PermissionDenied):
            admin_view(request)

    def test_editor_access_allowed(self):
        request = self.build_request(
            self.users["Editor"]
        )

        response = editor_view(request)

        self.assertEqual(response.status_code, 200)

    def test_viewer_denied_editor_access(self):
        request = self.build_request(
            self.users["Viewer"]
        )

        with self.assertRaises(PermissionDenied):
            editor_view(request)

    def test_dashboard_access_for_all_roles(self):
        for role, user in self.users.items():
            with self.subTest(role=role):
                request = self.build_request(user)

                response = dashboard_view(request)

                self.assertEqual(
                    response.status_code,
                    200,
                )

    def test_user_without_role_denied(self):
        request = self.build_request(
            self.no_role_user
        )

        with self.assertRaises(PermissionDenied):
            dashboard_view(request)

    def test_superuser_access_allowed(self):
        request = self.build_request(
            self.superuser
        )

        response = admin_view(request)

        self.assertEqual(response.status_code, 200)

    def test_inactive_user_denied(self):
        user = self.users["Admin"]
        user.is_active = False

        request = self.build_request(user)

        with self.assertRaises(PermissionDenied):
            admin_view(request)

    def test_invalid_role_configuration(self):
        with self.assertRaises(ValueError):
            role_required("UnknownRole")

    def test_empty_role_configuration(self):
        with self.assertRaises(ValueError):
            role_required()