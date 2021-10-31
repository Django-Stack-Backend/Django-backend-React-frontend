import json

import pytest
from rest_framework import status
from rest_framework.reverse import reverse
from safetydance import step_data
from safetydance_django.test import *
from safetydance_django.test import http_response
from safetydance_test import And, Given, Then, When, scripted_test

from .fixtures import *  # noqa
from .fixtures import (
    RESOURCE_ENDPOINT_DETAIL_NAME,
    RESOURCE_ENDPOINT_LIST_NAME,
    last_modified_for,
    role_todo_creator,
    serialize_page,
    serialize_resource,
    todo_creator_login,
)
from .steps import *


@pytest.mark.django_db
@scripted_test
def test_invalid_initial_state(admin_login):
    # TODO check the error response body for expected messages
    Given.http.force_authenticate(admin_login)
    When.http.post(
        reverse("todos-list"),
        data=json.dumps(
            {
                "title": "Buy milk",
                "status": "done",
                "priority": "medium",
                "assignee": "http://somewhere.example/someone",
            }
        ),
        content_type="application/json",
    )
    Then.http.status_code_is(status.HTTP_400_BAD_REQUEST)


@pytest.mark.django_db
@scripted_test
def test_valid_initial_state(admin_login):
    Given.http.force_authenticate(admin_login)
    When.http.post(
        reverse("todos-list"),
        data=json.dumps(
            {
                "title": "Buy milk",
                "status": "not started",
                "priority": "medium",
                "assignee": "http://somewhere.example/someone",
            }
        ),
        content_type="application/json",
    )
    Then.http.status_code_is(status.HTTP_201_CREATED)


@pytest.mark.django_db
@scripted_test
def test_invalid_state(admin_login):
    # TODO check the error response body for expected messages
    Given.http.force_authenticate(admin_login)
    When.http.post(
        reverse("todos-list"),
        data=json.dumps(
            {
                "title": "Buy milk",
                "status": "bogus status!!",
                "priority": "medium",
                "assignee": "http://somewhere.example/someone",
            }
        ),
        content_type="application/json",
    )
    Then.http.status_code_is(status.HTTP_400_BAD_REQUEST)

    When.http.post(
        reverse("todos-list"),
        data=json.dumps(
            {
                "title": "Buy milk",
                "status": "in progress",
                "priority": "not rated",
                "assignee": "http://somewhere.example/someone",
            }
        ),
        content_type="application/json",
    )
    Then.http.status_code_is(status.HTTP_400_BAD_REQUEST)

    When.http.post(
        reverse("todos-list"),
        data=json.dumps(
            {
                "title": "Buy milk",
                "status": "in progress",
                "priority": None,
                "assignee": "http://somewhere.example/someone",
            }
        ),
        content_type="application/json",
    )
    Then.http.status_code_is(status.HTTP_400_BAD_REQUEST)


@pytest.mark.django_db
@scripted_test
def test_invalid_transition(admin_login):
    # TODO check the error response body for expected messages
    data = {
        "title": "Buy milk",
        "status": "not started",
        "priority": "medium",
        "assignee": "http://somewhere.example/someone",
    }
    Given.http.force_authenticate(admin_login)
    When.http.post(
        reverse("todos-list"), data=json.dumps(data), content_type="application/json"
    )
    Then.http.status_code_is(status.HTTP_201_CREATED)

    url = http_response["Location"]
    Given.http.head(url)
    When.http.put(
        url,
        data=json.dumps(data),  # reflexive state transitions not allowed in this policy
        content_type="application/json",
        HTTP_IF_UNMODIFIED_SINCE=http_response["Last-Modified"],
        HTTP_IF_MATCH=http_response["Etag"],
    )
    Then.http.status_code_is(status.HTTP_200_OK)

    data["status"] = "in progress"
    Given.http.head(url)
    When.http.put(  # transition to "in progress"
        url,
        data=json.dumps(data),
        content_type="application/json",
        HTTP_IF_UNMODIFIED_SINCE=http_response["Last-Modified"],
        HTTP_IF_MATCH=http_response["Etag"],
    )
    Then.http.status_code_is(status.HTTP_200_OK)

    data["status"] = "not started"
    Given.http.head(url)
    When.http.put(  # invalid transition to "not started" from "in progress"
        url,
        data=json.dumps(data),
        content_type="application/json",
        HTTP_IF_UNMODIFIED_SINCE=http_response["Last-Modified"],
        HTTP_IF_MATCH=http_response["Etag"],
    )
    Then.http.status_code_is(status.HTTP_400_BAD_REQUEST)


@pytest.mark.django_db
@scripted_test
def test_valid_transition(admin_login):
    data = {
        "title": "Buy milk",
        "status": "not started",
        "priority": "medium",
        "assignee": "http://somewhere.example/someone",
    }
    Given.http.force_authenticate(admin_login)
    When.http.post(
        reverse("todos-list"), data=json.dumps(data), content_type="application/json"
    )
    Then.http.status_code_is(status.HTTP_201_CREATED)
    url = http_response["Location"]

    data["status"] = "in progress"
    Given.http.head(url)
    When.http.put(  # transition to "in progress"
        url,
        data=json.dumps(data),
        content_type="application/json",
        HTTP_IF_UNMODIFIED_SINCE=http_response["Last-Modified"],
        HTTP_IF_MATCH=http_response["Etag"],
    )
    Then.http.status_code_is(status.HTTP_200_OK)

    data["status"] = "blocked"
    data["blockers"] = [{"explanation": "Because I said so, perhaps..."}]
    Given.http.head(url)
    When.http.put(  # invalid transition to "not started" from "in progress"
        url,
        data=json.dumps(data),
        content_type="application/json",
        HTTP_IF_UNMODIFIED_SINCE=http_response["Last-Modified"],
        HTTP_IF_MATCH=http_response["Etag"],
    )
    Then.http.status_code_is(status.HTTP_200_OK)


@pytest.mark.django_db
@scripted_test
def test_unauthorized_transition(todo_creator_login):
    data = {
        "title": "Buy milk",
        "status": "not started",
        "priority": "medium",
        "assignee": "http://somewhere.example/someone",
    }
    Given.http.force_authenticate(todo_creator_login)
    When.http.post(
        reverse("todos-list"), data=json.dumps(data), content_type="application/json"
    )
    Then.http.status_code_is(status.HTTP_201_CREATED)
    url = http_response["Location"]

    data["status"] = "in progress"
    Given.http.head(url)
    When.http.put(  # transition to "in progress"
        url,
        data=json.dumps(data),
        content_type="application/json",
        HTTP_IF_UNMODIFIED_SINCE=http_response["Last-Modified"],
        HTTP_IF_MATCH=http_response["Etag"],
    )
    Then.http.status_code_is(status.HTTP_400_BAD_REQUEST)


@pytest.mark.django_db
@scripted_test
def test_authorized_transition(todo_creator_login):
    data = {
        "title": "Buy milk",
        "status": "not started",
        "priority": "medium",
        "assignee": "http://somewhere.example/someone",
    }
    Given.http.force_authenticate(todo_creator_login)
    When.http.post(
        reverse("todos-list"), data=json.dumps(data), content_type="application/json"
    )
    Then.http.status_code_is(status.HTTP_201_CREATED)
    url = http_response["Location"]

    data["status"] = "canceled"
    Given.http.head(url)
    When.http.put(  # transition to "in progress"
        url,
        data=json.dumps(data),
        content_type="application/json",
        HTTP_IF_UNMODIFIED_SINCE=http_response["Last-Modified"],
        HTTP_IF_MATCH=http_response["Etag"],
    )
    Then.http.status_code_is(status.HTTP_200_OK)
