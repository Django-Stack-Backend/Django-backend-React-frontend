import json
from copy import copy

import pytest
from django.urls import reverse
from rest_framework import status
from safetydance_django.test import *  # noqa: F403, F401
from safetydance_django.test import http_response
from safetydance_test import And, Given, Then, scripted_test

from scrud_django.registration import ResourceRegistration

from .fixtures import *  # noqa
from .fixtures import (
    RESOURCE_ENDPOINT_DETAIL_NAME,
    RESOURCE_ENDPOINT_LIST_NAME,
    last_modified_for,
    serialize_page,
    serialize_resource,
)
from .steps import *  # noqa: F403, F401

# TESTS


@pytest.mark.django_db
@scripted_test
def test_resource_get_list(regular_login, partner_profiles):
    url = reverse(RESOURCE_ENDPOINT_LIST_NAME)
    assert url == '/partner-profiles/'

    Given.http.force_authenticate(regular_login)
    And.http.get(url)
    Then.http.status_code_is(status.HTTP_200_OK)
    And.http.content_type_is('application/json')
    And.http.response_json_is(serialize_page([partner_profiles]))
    http_response.get('last-modified') == last_modified_for(partner_profiles)


@pytest.mark.django_db
@scripted_test
def test_resource_get_detail(regular_login, partner_profiles):
    url = reverse(RESOURCE_ENDPOINT_DETAIL_NAME, kwargs={'slug': partner_profiles.id},)
    assert url == f'/partner-profiles/{partner_profiles.id}/'

    Given.http.force_authenticate(regular_login)
    And.http.get(url)
    Then.http.status_code_is(status.HTTP_200_OK)
    And.http.content_type_is('application/json')
    And.http.response_json_is(serialize_resource(partner_profiles))
    http_response.get('last-modified') == last_modified_for(partner_profiles)


@pytest.mark.django_db
@scripted_test
def test_resource_post(admin_login, partner_profile_post_data):
    url = reverse(RESOURCE_ENDPOINT_LIST_NAME)
    assert url == '/partner-profiles/'

    serialized_data = partner_profile_post_data

    Given.http.force_authenticate(admin_login)
    And.http.post(
        url,
        data=json.dumps(partner_profile_post_data),
        content_type='application/json',
    )
    Then.http.status_code_is(status.HTTP_201_CREATED)
    And.http.content_type_is('application/json')
    And.http.resource_json_is(serialized_data)


@pytest.mark.django_db
@scripted_test
def test_resource_post_bad_request(admin_login, partner_profile_post_data):
    url = reverse(RESOURCE_ENDPOINT_LIST_NAME)
    assert url == '/partner-profiles/'

    serialized_data = dict(partner_profile_post_data)
    serialized_data['logo'] = 42  # must be a string and valid URI

    Given.http.force_authenticate(admin_login)
    And.http.post(
        url, data=json.dumps(serialized_data), content_type='application/json',
    )
    Then.http.status_code_is(status.HTTP_400_BAD_REQUEST)
    And.http.content_type_is('application/problem+json')
    And.http.response_json_matches(
        {
            "type": "https://api.openteams.com/http-problem/json-invalid",
            "title": "JSON Validation Error",
            "name": "data.logo",
            "value": 42,
            "rule": "type",
            "rule_definition": "string",
        }
    )


@pytest.mark.django_db
@scripted_test
def test_resource_put(admin_login, partner_profiles, partner_profile_post_data):
    resource = ResourceRegistration.register(
        content=partner_profile_post_data, register_type='partner-profiles'
    )

    partner_profile_put_data = copy(partner_profile_post_data)
    partner_profile_put_data['name'] = 'test put'
    partner_profile_put_data['slug'] = 'test-put'
    partner_profile_put_data['display_name'] = 'Test PUT'

    serialized_data = partner_profile_put_data

    url = reverse(RESOURCE_ENDPOINT_DETAIL_NAME, kwargs={'slug': resource.id})
    assert url == f'/partner-profiles/{resource.id}/'

    Given.http.force_authenticate(admin_login)
    And.http.get(url)
    response = http_response
    And.http.put(
        url,
        data=json.dumps(partner_profile_put_data),
        content_type='application/json',
        HTTP_IF_UNMODIFIED_SINCE=response["Last-Modified"],
        HTTP_IF_MATCH=response["ETag"],
    )
    Then.http.status_code_is(status.HTTP_200_OK)
    And.http.content_type_is('application/json')
    And.http.resource_json_is(serialized_data)


@pytest.mark.django_db
@scripted_test
def test_resource_delete(admin_login, partner_profile_post_data):
    resource = ResourceRegistration.register(
        content=partner_profile_post_data, register_type='partner-profiles'
    )

    url = reverse(RESOURCE_ENDPOINT_DETAIL_NAME, kwargs={'slug': resource.id})
    assert url == f'/partner-profiles/{resource.id}/'

    Given.http.force_authenticate(admin_login)
    And.http.get(url)
    response = http_response
    And.http.delete(
        url,
        HTTP_IF_UNMODIFIED_SINCE=response["Last-Modified"],
        HTTP_IF_MATCH=response["ETag"],
    )
    Then.http.status_code_is(status.HTTP_204_NO_CONTENT)


# JSON SCHEMA

JSON_SCHEMA_ENDPOINT_PREFIX = "json-schema"
JSON_SCHEMA_ENDPOINT_DETAIL_NAME = f"{JSON_SCHEMA_ENDPOINT_PREFIX}-detail"
JSON_SCHEMA_ENDPOINT_LIST_NAME = f"{JSON_SCHEMA_ENDPOINT_PREFIX}-list"


@pytest.mark.django_db
@scripted_test
def test_js_schema_get_list(regular_login):
    url = reverse(JSON_SCHEMA_ENDPOINT_LIST_NAME)
    assert url == '/json-schema/'

    Given.http.force_authenticate(regular_login)
    And.http.get(url)
    Then.http.status_code_is(status.HTTP_200_OK)
    And.http.content_type_is('application/json')
    And.http.response_json_is({})


# JSON LD

JSON_LD_ENDPOINT_PREFIX = "json-ld"
JSON_LD_ENDPOINT_DETAIL_NAME = f"{JSON_LD_ENDPOINT_PREFIX}-detail"
JSON_LD_ENDPOINT_LIST_NAME = f"{JSON_LD_ENDPOINT_PREFIX}-list"


@pytest.mark.django_db
@scripted_test
def test_js_ld_get_list(regular_login):
    url = reverse(JSON_LD_ENDPOINT_LIST_NAME)
    assert url == '/json-ld/'

    Given.http.force_authenticate(regular_login)
    And.http.get(url)
    Then.http.status_code_is(status.HTTP_200_OK)
    And.http.content_type_is('application/json')
    And.http.response_json_is({})
