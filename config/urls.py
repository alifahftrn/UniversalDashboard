from django.contrib import admin
from django.urls import include, path


admin.site.site_header = "Universal Dashboard Studio"
admin.site.site_title = "UDS Administration"
admin.site.index_title = "Administration Workspace"


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
]