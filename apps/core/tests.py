from django.test import SimpleTestCase
from django.urls import reverse


class CorePageTests(SimpleTestCase):

    def test_overview(self):
        response = self.client.get(
            reverse("core:overview")
        )

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "core/overview.html"
        )

    def test_navigation_pages(self):
        pages = [
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

        for page in pages:
            with self.subTest(page=page):

                response = self.client.get(
                    reverse(f"core:{page}")
                )

                self.assertEqual(
                    response.status_code,
                    200
                )