"""Tests to validate that the endpoints are returning valid JSON-LD with the expected
and desired properties
"""
import pytest
from django.urls import reverse
from rdflib import URIRef
from rest_framework import status
from safetydance_django.test import *  # noqa: F403, F401
from safetydance_test import And, Then, When, scripted_test

from scrud_django import collection_type_uri_for

from .fixtures import *  # noqa
from .fixtures import RESOURCE_ENDPOINT_LIST_NAME
from .steps import *  # noqa: F403, F401
from .steps import json_path_match

type_resource_collection = URIRef(
    "https://api.openteams.com/json-ld/ResourceCollection"
)
type_partner_profiles_collection = URIRef(
    collection_type_uri_for("tests://PartnerProfiles")
)
type_partner_profile = URIRef("tests://PartnerProfiles")


@pytest.mark.django_db
@scripted_test
def test_collection_json_ld():
    url = reverse(RESOURCE_ENDPOINT_LIST_NAME)
    assert url == '/partner-profiles/'

    When.http.options(url)
    Then.http.status_code_is(status.HTTP_200_OK)
    And.json_path_matches(
        "get.responses['200'].content['application/json'].context",
        lambda x: x is not None and x != "",
    )
    context_url = json_path_match[0].value

    When.http.get(context_url)
    Then.http.status_code_is(status.HTTP_200_OK)
    And.ld_context_states_sub_class_of(
        type_partner_profiles_collection, type_resource_collection
    )


@pytest.mark.django_db
@scripted_test
def test_detail_json_ld(admin_login):
    url = reverse(RESOURCE_ENDPOINT_LIST_NAME)
    assert url == '/partner-profiles/'

    When.http.options(url)
    Then.http.status_code_is(status.HTTP_200_OK)
    And.json_path_matches(
        "post.requestBody.content['application/json'].context",
        lambda x: x is not None and x != "",
    )
    context_url = json_path_match[0].value

    # the context resource may be protected in our configuration.
    When.http.force_authenticate(admin_login)
    When.http.get(context_url)
    Then.http.status_code_is(status.HTTP_200_OK)
    # TODO add more validation
