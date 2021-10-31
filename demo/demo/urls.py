import importlib.resources

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from scoped_rbac.rest import UserViewSet
from scrud_django import registration

app_name = "scrud_django-demo"

router = DefaultRouter()
router.register(r"users", UserViewSet)

api_urlpatterns = [
    path("", include(router.urls), name="api"),
    path("", include("scrud_django.urls")),
]
api_urlpatterns.extend(
    registration.resource_types(
        registration.json_resource_type(
            resource_type_uri="tests://PartnerProfiles",
            revision="1",
            slug="partner-profiles",
            schema_func=lambda: importlib.resources.read_text(
                "demo", "PartnerProfile-schema.json"
            ),
            context_func=lambda: importlib.resources.read_text(
                "demo", "PartnerProfile-ld.json"
            ),
        ),
    )
)

urlpatterns = [
    path("api/", include(api_urlpatterns)),
]