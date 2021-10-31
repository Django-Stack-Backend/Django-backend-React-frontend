from rest_framework.reverse import reverse

from scrud_django.utils import link_content


def get_schema_uri_for(resource_type, request):
    uri = None
    # prefer a local version to a remote version
    if resource_type.schema:
        schema = resource_type.schema
        uri = reverse(
            schema.resource_type.route_name_detail(), args=[schema.id], request=request,
        )
    elif resource_type.schema_uri:
        uri = resource_type.schema_uri
    return uri


def get_context_uri_for(resource_type, request):
    uri = None
    # prefer a local version to a remote version
    if resource_type.context:
        context = resource_type.context
        uri = reverse(
            context.resource_type.route_name_detail(),
            args=[context.id],
            request=request,
        )
    elif resource_type.context_uri:
        uri = resource_type.context_uri
    return uri


def get_link_header_for(resource_type, request):
    schema_uri = get_schema_uri_for(resource_type, request)
    context_uri = get_context_uri_for(resource_type, request)
    schema_link = (
        link_content(schema_uri, "describedBy", "application/json")
        if schema_uri
        else ""
    )
    context_link = (
        link_content(
            context_uri, "http://www.w3.org/ns/json-ld#context", "application/ld+json",
        )
        if context_uri
        else ""
    )
    join_links = ", " if schema_link and context_link else ""
    return schema_link + join_links + context_link
