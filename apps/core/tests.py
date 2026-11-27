from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class CorePageTests(TestCase):

    pages = [
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
    ]

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="test_user",
            password="TestPassword123!",
        )

    def test_anonymous_user_redirected_to_login(self):
        login_url = reverse("accounts:login")

        for page in self.pages:
            with self.subTest(page=page):
                url = reverse(f"core:{page}")
                response = self.client.get(url)

                self.assertRedirects(
                    response,
                    f"{login_url}?next={url}",
                )

    def test_authenticated_overview(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("core:overview")
        )

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "core/overview.html",
        )

    def test_authenticated_navigation_pages(self):
        self.client.force_login(self.user)

        for page in self.pages:
            with self.subTest(page=page):
                response = self.client.get(
                    reverse(f"core:{page}")
                )

                self.assertEqual(
                    response.status_code,
                    200,
                )