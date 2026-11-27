from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


User = get_user_model()


class AuthenticationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.password = "TestPassword123!"

        cls.user = User.objects.create_user(
            username="test_user",
            email="test@example.com",
            password=cls.password,
        )

        cls.inactive_user = User.objects.create_user(
            username="inactive_user",
            password=cls.password,
            is_active=False,
        )

    def test_login_page_accessible(self):
        response = self.client.get(
            reverse("accounts:login")
        )

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "accounts/login.html",
        )

    def test_login_with_valid_credentials(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": self.user.username,
                "password": self.password,
            },
        )

        self.assertRedirects(
            response,
            reverse("core:overview"),
        )

        self.assertIn(
            "_auth_user_id",
            self.client.session,
        )

    def test_login_with_invalid_password(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": self.user.username,
                "password": "wrong-password",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Invalid username or password.",
        )

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    def test_inactive_user_cannot_login(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": self.inactive_user.username,
                "password": self.password,
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    def test_authenticated_user_redirected_from_login(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("accounts:login")
        )

        self.assertRedirects(
            response,
            reverse("core:overview"),
        )

    def test_login_redirects_to_requested_page(self):
        target = reverse("core:database-connections")

        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": self.user.username,
                "password": self.password,
                "next": target,
            },
        )

        self.assertRedirects(response, target)

    def test_external_redirect_is_rejected(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": self.user.username,
                "password": self.password,
                "next": "https://example.com",
            },
        )

        self.assertRedirects(
            response,
            reverse("core:overview"),
        )

    def test_logout_successful(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:logout")
        )

        self.assertRedirects(
            response,
            reverse("accounts:login"),
        )

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    def test_logout_get_method_rejected(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("accounts:logout")
        )

        self.assertEqual(response.status_code, 405)

    def test_protected_page_after_logout(self):
        self.client.force_login(self.user)

        self.client.post(
            reverse("accounts:logout")
        )

        response = self.client.get(
            reverse("core:overview")
        )

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next=/",
        )

    def test_login_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)

        response = client.post(
            reverse("accounts:login"),
            {
                "username": self.user.username,
                "password": self.password,
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_logout_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)

        response = client.post(
            reverse("accounts:logout")
        )

        self.assertEqual(response.status_code, 403)