import importlib.resources

from django.urls import include, path

from scrud_django import registration
from .resource_types import json_resource_types

urlpatterns = [path("", include("scrud_django.urls"))]
urlpatterns.extend(registration.resource_types(*json_resource_types()))