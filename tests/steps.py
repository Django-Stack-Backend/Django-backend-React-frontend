import json
from datetime import datetime

from django.db.models import Model
from jsonpath_ng import parse
from rdflib import Graph, URIRef
from safetydance import step_data
from safetydance_django.steps import (  # noqa: F401
    http_client,
    http_response,
    json_values_match,
)
from safetydance_django.test import Http  # noqa: F401
from safetydance_test.step_extension import step_extension

from scrud_django.models import Resource, ResourceType

__all__ = [
    'an_instance_named',
    'is_valid_resource',
    'is_valid_resource_type',
    'an_registration_data',
    'check_registration_results',
    'json_path_expressions',
    'json_path_match',
    'json_path_matches',
    'ld_context_states_sub_class_of',
    'named_instances',
    'resource_json_is',
    'response_json_matches',
]


named_instances = step_data(dict, initializer=dict)
json_path_expressions = step_data(dict, initializer=dict)
json_path_match = step_data(object)


sub_class_of = URIRef("http://www.w3.org/2000/01/rdf-schema#subClassOf")


@step_extension
def an_instance_named(name: str, instance: Model):
    named_instances[name] = instance


@step_extension
def is_valid_resource(name: str):
    instance = named_instances[name]
    assert isinstance(instance, Resource)
    assert isinstance(instance.content, dict)
    assert isinstance(instance.modified_at, datetime)
    assert isinstance(instance.etag, str)
    assert len(instance.etag) == 32


@step_extension
def is_valid_resource_type(name: str):
    instance = named_instances[name]
    assert isinstance(instance, ResourceType)
    assert isinstance(instance.type_uri, str)
    assert len(instance.type_uri) > 0


@step_extension
def ld_context_states_sub_class_of(subclass_uri, superclass_uri):
    data = http_response.json()
    g = Graph().parse(data=json.dumps(data), format='json-ld')
    superclasses = list(g.transitive_objects(subclass_uri, sub_class_of))
    assert len(superclasses) > 0, superclasses
    assert superclass_uri in superclasses, superclasses


# register

named_registration_data = step_data(dict, initializer=dict)


@step_extension
def an_registration_data(name: str, registration_data: dict):
    named_registration_data[name] = registration_data


@step_extension
def check_registration_results(name: str, result):
    expected = named_registration_data[name]
    # result = register_resource_type(**expected)
    resource_type_name = list(expected.keys())[0]
    expected = expected[resource_type_name]

    assert result.type_uri == expected['rdf_type_uri']
    assert result.slug == resource_type_name
    assert result.context_uri == expected['json_ld_context_url']
    assert result.schema_uri == expected['json_schema_url']


def get_compiled_expression(expr, compiled_expressions):
    compiled_expr = compiled_expressions.get(expr, None)
    if compiled_expr is None:
        compiled_expr = parse(expr)
        compiled_expressions[expr] = compiled_expr
    return compiled_expr


@step_extension
def json_path_matches(expr, condition):
    data = http_response.json()
    compiled_expr = get_compiled_expression(expr, json_path_expressions)
    json_path_match = compiled_expr.find(data)
    assert len(json_path_match) > 0, data
    match = json_path_match[0].value
    assert condition(
        json_path_match
    ), f"expr: {expr} \ncondition: {condition}, \n match: {match}"


def resource_envelope_json_is(resource_data: dict):
    assert 'href' in resource_data
    assert isinstance(resource_data['href'], str)

    assert 'last_modified' in resource_data
    assert isinstance(resource_data['last_modified'], str)

    assert 'etag' in resource_data
    assert isinstance(resource_data['etag'], str)

    assert 'content' in resource_data
    assert isinstance(resource_data['content'], dict)

    response = http_response.json()
    assert response["content"] == resource_data["content"]


def resource_json_is(resource_data):
    response = http_response.json()
    assert response == resource_data, response


def response_json_matches(expected):
    observed = http_response.json()
    assert json_values_match(expected, observed), http_response


resource_envelope_json_is = step_extension(
    f=resource_envelope_json_is, target_type=Http
)
resource_json_is = step_extension(f=resource_json_is, target_type=Http)
response_json_matches = step_extension(f=response_json_matches, target_type=Http)
