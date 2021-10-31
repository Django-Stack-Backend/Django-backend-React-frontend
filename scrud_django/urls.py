"""SCRUD DJANGO URL Configuration."""
import logging
from itertools import chain

from django.db.utils import OperationalError, ProgrammingError
from django.urls import include, path

from scoped_rbac.models import Role, RoleAssignment
from scrud_django import registration, services, collection_type_uri_for
from scrud_django.views import (
    ResourceCollectionContextView,
    ResourceCollectionSchemaView,
    get_service_list,
)

urlpatterns = [
    path("services/", get_service_list, name="services"),
    path(
        "collections-json-schema/<str:slug>/",
        ResourceCollectionSchemaView.as_view(),
        name="collections-json-schema",
    ),
    path(
        "collections-json-ld/<str:slug>/",
        ResourceCollectionContextView.as_view(),
        name="collections-json-ld",
    ),
    path("", include("scoped_rbac.urls")),
]

try:
    registration.register_json_schema_resource_type()
    registration.register_json_ld_resource_type()
    registration.register_indexing_policy_resource_type()
    registration.workflow_policy_resource_type()

    urlpatterns.extend(chain(
        registration.JSON_SCHEMA_REGISTRATION_.urls,
        registration.JSON_LD_REGISTRATION_.urls,
        registration.INDEXING_POLICY_REGISTRATION_.urls,
        registration.WORKFLOW_POLICY_REGISTRATION_.urls,
    ))
except (OperationalError, ProgrammingError) as e:
    logging.error(e)

services.add_service(collection_type_uri_for(Role.resource_type.iri), "role")
services.add_service(collection_type_uri_for(RoleAssignment.resource_type.iri), "roleassignment")