import json
import os
from datetime import timezone
from http import server
from multiprocessing import Process
from uuid import uuid4

import pytest
from django.urls import reverse
from django.utils.http import http_date, quote_etag
from django.utils.timezone import now
from scoped_rbac.models import Role, RoleAssignment
from scoped_rbac.permissions import DEFAULT_CONTEXT

from scrud_django.registration import ResourceRegistration

from .factories import UserFactory

__all__ = [
    'ROOT_PATH',
    'DATA_PATH',
    'RESOURCE_ENDPOINT_PREFIX',
    'RESOURCE_ENDPOINT_DETAIL_NAME',
    'RESOURCE_ENDPOINT_LIST_NAME',
    'admin_login',
    'http_static_server',
    'last_modified_for',
    'login_no_roles',
    'partner_profile_post_data',
    'partner_profiles',
    'regular_login',
    'role_allow_all',
    'serialize_page',
    'serialize_resource_envelope',
    'serialize_resource',
]

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(ROOT_PATH, 'data')


# RESOURCE

RESOURCE_ENDPOINT_PREFIX = "partner-profiles"
RESOURCE_ENDPOINT_DETAIL_NAME = f"{RESOURCE_ENDPOINT_PREFIX}-detail"
RESOURCE_ENDPOINT_LIST_NAME = f"{RESOURCE_ENDPOINT_PREFIX}-list"


def last_modified_for(resource):
    return http_date(resource.modified_at.replace(tzinfo=timezone.utc).timestamp())


def serialize_page(resources):
    return {
        'count': 1,
        'page_count': 1,
        'next': None,
        'previous': None,
        'content': [serialize_resource_envelope(resource) for resource in resources],
    }


def serialize_resource_envelope(resource):
    return {
        'content': resource.content,
        'last_modified': last_modified_for(resource),
        'etag': quote_etag(resource.etag),
        'href': "http://testserver"
        + reverse(RESOURCE_ENDPOINT_DETAIL_NAME, args=[resource.id]),
    }


def serialize_resource(resource):
    return resource.content


@pytest.mark.django_db
@pytest.fixture
def role_allow_all():
    role = Role(definition=True, etag=uuid4().hex, modified_at=now(),)
    role.save()
    return role


@pytest.mark.django_db
@pytest.fixture
def role_todo_creator():
    role = Role(
        definition = {
            "http.GET": [ "tests://ToDo" ],
            "http.POST": [ "tests://ToDo" ],
            "http.PUT": {
                "tests://ToDo": {
                    "condition": {
                        "operator": "scrud_workflow",
                        "authorized_transitions": ["cancel"],
                    }
                }
            }
        },
        etag=uuid4().hex,
        modified_at=now(),
    )
    role.save()
    return role


@pytest.mark.django_db
@pytest.fixture
def regular_login(role_allow_all):
    user = UserFactory()
    RoleAssignment(
        user=user,
        role=role_allow_all,
        rbac_context="",
        etag=uuid4().hex,
        modified_at=now(),
    ).save()
    return user


@pytest.mark.django_db
@pytest.fixture
def admin_login():
    return UserFactory(is_staff=True, is_superuser=True)


@pytest.mark.django_db
@pytest.fixture
def login_no_roles():
    return UserFactory()


@pytest.mark.django_db
@pytest.fixture
def todo_creator_login(role_todo_creator):
    user = UserFactory()
    RoleAssignment(
        user=user,
        role=role_todo_creator,
        rbac_context=DEFAULT_CONTEXT,
        etag=uuid4().hex,
        modified_at=now(),
    ).save()
    return user


def http_process_server():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    os.chdir(path)
    server_address = ('localhost', 8123)
    httpd = server.HTTPServer(server_address, server.SimpleHTTPRequestHandler)
    httpd.serve_forever()


@pytest.fixture
def http_static_server():
    p = Process(target=http_process_server, args=())
    p.start()

    yield

    p.join(timeout=1)
    p.kill()


@pytest.fixture
def partner_profile_post_data():
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'static',
        'post_partner_profile.json',
    )
    with open(path, 'r') as f:
        return json.loads(f.read())


@pytest.mark.django_db
@pytest.fixture
def partner_profiles(partner_profile_post_data):
    # force registration of resource types
    reverse(RESOURCE_ENDPOINT_LIST_NAME)
    return ResourceRegistration.register(
        content=partner_profile_post_data, register_type='partner-profiles'
    )
