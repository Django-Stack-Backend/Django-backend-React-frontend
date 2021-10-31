from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from scoped_rbac.rest import AccessControlledAPIView

from scrud_django import collection_type_uri_for, services
from scrud_django.decorators import scrudful_api_view, scrudful_viewset
from scrud_django.mixins.view_mixins import ResourceViewMixin
from scrud_django.models import Resource
from scrud_django.registration import get_resource_type_for
from scrud_django.validators import JsonValidator


@scrudful_viewset
class ResourceViewSet(
    AccessControlledAPIView, ResourceViewMixin, viewsets.ModelViewSet
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resource_type_name = kwargs.get('resource_type_name')
        self.validator = JsonValidator()

    @property
    def resource_type_iri(self):
        resource_type = self.get_resource_type()
        return resource_type.type_uri

    @property
    def list_type_iri(self):
        return collection_type_uri_for(self.resource_type_iri)


@scrudful_viewset
class ResourceViewSetGenericFilter(
    AccessControlledAPIView, ResourceViewMixin, viewsets.ModelViewSet
):
    filter_backends = [DjangoFilterBackend]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resource_type_name = kwargs.get('resource_type_name')
        self.validator = JsonValidator()

    def list(self, request):
        """Return the resource for the given resource type name."""
        resource_type = self.get_resource_type()

        query_filter = dict(request.GET.items())

        queryset = Resource.objects.filter(resource_type=resource_type).filter(
            content__contains=query_filter
        )

        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return Response(self.get_paginated_response(serializer.data))

        serializer = self.get_serializer(instance=queryset, many=True)
        return Response(serializer.data)

    @property
    def resource_type_iri(self):
        resource_type = self.get_resource_type()
        return resource_type.type_uri

    @property
    def list_type_iri(self):
        return collection_type_uri_for(self.resource_type_iri)


class ResourceCollectionSchemaView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug: str):
        resource_type = get_resource_type_for(slug)

        if resource_type.schema:
            content_defn = resource_type.schema.content
        elif resource_type.schema_uri:
            content_defn = {"$ref": resource_type.schema_uri}
        else:
            content_defn = {"type": "any"}

        schema = {
            "$id": "https://api.openteams.com/json-schema/ResourceCollection"
            f"?contents_type={resource_type.type_uri}",
            "$schema": "http://json-schema.org/draft-04/schema",
            "description": f"A listing of resources of type {resource_type.type_uri}.",
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "The total number of items in the collection.",
                },
                "page_count": {
                    "type": "integer",
                    "description": "The total number of pages in the collection.",
                },
                "first": {
                    "type": "string",
                    "format": "uri",
                    "description": "URL of the first page.",
                },
                "previous": {
                    "type": "string",
                    "format": "uri",
                    "description": "URL of the previous page, if any.",
                },
                "next": {
                    "type": "string",
                    "format": "uri",
                    "description": "URL of the next page, if any.",
                },
                "last": {
                    "type": "string",
                    "format": "uri",
                    "description": "URL of the last page.",
                },
                "content": {
                    "properties": {
                        "type": "array",
                        "description": f"Listing of {resource_type.type_uri} "
                        "resources in Envelopes.",
                        "items": {
                            "properties": {
                                "href": {
                                    "type": "string",
                                    "format": "uri",
                                    "description": "URL of the nested resource.",
                                },
                                "etag": {
                                    "type": "string",
                                    "description": "HTTP ETag header of the nested "
                                    "resource.",
                                },
                                "last_modified": {
                                    "type": "string",
                                    "description": "HTTP Last-Modified header of the "
                                    "nested resource.",
                                },
                                "content": content_defn,
                            },
                        },
                    },
                },
            },
        }

        return Response(schema)


class ResourceCollectionContextView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug: str):
        resource_type = get_resource_type_for(slug)
        return Response(
            {
                "openteams": "https://api.openteams.com/json-ld/",
                "@id": collection_type_uri_for(resource_type.type_uri),
                "http://www.w3.org/2000/01/rdf-schema#subClassOf": {
                    "@id": "https://api.openteams.com/json-ld/ResourceCollection"
                },
                "count": {"@id": "openteams:count"},
                "page_count": {"@id": "openteams:page_count"},
                "first": {"@id": "opententeams:first"},
                "previous": {"@id": "opententeams:previous"},
                "next": {"@id": "opententeams:next"},
                "last": {"@id": "opententeams:last"},
                "content": {
                    "@id": "openteams:Envelope",
                    "@container": "@list",
                    "openteams:envelopeContents": resource_type.type_uri,
                },
            }
        )


@scrudful_api_view(
    etag_func=lambda *args, **kwargs: services.etag,
    last_modified_func=lambda *args, **kwargs: services.last_modified,
)
@permission_classes([AllowAny])
def get_service_list(request, *args, **kwargs):
    catalog = {}
    for type_uri, url_func in services.services.items():
        catalog[type_uri] = url_func(request=request)
    return Response(catalog)
