from typing import Optional

import reversion
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.reverse import reverse

from scrud_django.headers import get_context_uri_for, get_schema_uri_for
from scrud_django.models import Resource
from scrud_django.paginations import StandardResultsSetPagination
from scrud_django.registration import (
    ResourceRegistration,
    get_resource_type_for,
)
from scrud_django.serializers import ResourceSerializer


class ResourceViewMixin:
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    pagination_class = StandardResultsSetPagination

    # scrud variable
    resource_type_name: Optional[str] = None

    class Meta:
        def etag_func(view_instance, request, slug: str):
            instance = view_instance.get_instance(request, slug)
            return instance.etag

        def last_modified_func(view_instance, request, slug: str):
            instance = view_instance.get_instance(request, slug)
            return instance.modified_at

        def schema_link_or_func(view_instance, request, slug: str = None):
            if view_instance.resource_type_name:
                resource_type = view_instance.get_resource_type()
                return get_schema_uri_for(resource_type, request)
            return None

        def context_link_or_func(view_instance, request, slug: str = None):
            if view_instance.resource_type_name:
                resource_type = view_instance.get_resource_type()
                return get_context_uri_for(resource_type, request)
            return None

        def list_etag_func(view_instance, request, *args, **kwargs):
            resource_type = view_instance.get_resource_type()
            return resource_type.etag

        def list_last_modified_func(view_instance, request, *args, **kwargs):
            resource_type = view_instance.get_resource_type()
            return resource_type.modified_at

        def list_schema_link_or_func(view_instance, request, *args, **kwargs):
            resource_type = view_instance.get_resource_type()
            return reverse(
                "collections-json-schema", args=[resource_type.slug], request=request,
            )

        def list_context_link_or_func(view_instance, request, *args, **kwargs):
            resource_type = view_instance.get_resource_type()
            return reverse(
                "collections-json-ld", args=[resource_type.slug], request=request,
            )

    def get_resource_type(self):
        return get_resource_type_for(self.resource_type_name)

    def get_instance(self, request, slug: str):
        resource_type = self.get_resource_type()
        instance = get_object_or_404(
            Resource, resource_type=resource_type, pk=int(slug)
        )
        return instance

    def get_serializer(self, *args, **kwargs):
        kwargs["resource_type"] = self.get_resource_type()
        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        if self.get_resource_type().uses_reversion:
            with reversion.create_revision():
                response = serializer.save()
                reversion.set_comment('Add Resource')
            return response
        return serializer.save()

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = {
            'Location': reverse(
                serializer.instance.resource_type.route_name_detail(),
                args=[serializer.instance.id],
                request=request,
            )
        }
        return Response(
            serializer.data, headers=headers, status=status.HTTP_201_CREATED
        )

    def update(self, request, slug: str):
        """Update a Resource."""
        instance = self.get_instance(request, slug)
        serializer = self.get_serializer(
            data=request.data, instance=instance, many=False
        )
        serializer.is_valid(raise_exception=True)
        instance = ResourceRegistration.update(
            content=request.data, register_type=self.resource_type_name, slug=slug,
        )
        serializer = self.get_serializer(instance=instance, many=False)
        return Response(serializer.data)

    def destroy(self, request, slug: str):
        """Update a Resource."""
        ResourceRegistration.delete(
            register_type=self.resource_type_name, slug=slug,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, slug: str):
        """Return the resource for the given resource type name."""
        instance = self.get_instance(request, slug)
        serializer = self.get_serializer(instance=instance, many=False)
        return Response(serializer.data)

    def list(self, request):
        """Return the resource for the given resource type name."""
        resource_type = self.get_resource_type()

        queryset = Resource.objects.filter(resource_type=resource_type)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return Response(self.get_paginated_response(serializer.data))

        serializer = self.get_serializer(instance=queryset, many=True)
        return Response(serializer.data)


class GenericViewMixin:

    # scrud variable
    resource_type_name: Optional[str] = None

    class Meta:
        def etag_func(view_instance, request, slug: str):
            instance = view_instance.get_instance(request, slug)
            return instance.etag

        def last_modified_func(view_instance, request, slug: str):
            instance = view_instance.get_instance(request, slug)
            return instance.modified_at

        def schema_link_or_func(view_instance, request, slug: str = None):
            if view_instance.resource_type_name:
                resource_type = view_instance.get_resource_type()
                return get_schema_uri_for(resource_type, request)
            return None

        def context_link_or_func(view_instance, request, slug: str = None):
            if view_instance.resource_type_name:
                resource_type = view_instance.get_resource_type()
                return get_context_uri_for(resource_type, request)
            return None

        def list_etag_func(view_instance, request, *args, **kwargs):
            resource_type = view_instance.get_resource_type()
            return resource_type.etag

        def list_last_modified_func(view_instance, request, *args, **kwargs):
            resource_type = view_instance.get_resource_type()
            return resource_type.modified_at

        def list_schema_link_or_func(view_instance, request, *args, **kwargs):
            resource_type = view_instance.get_resource_type()
            return reverse(
                "collections-json-schema", args=[resource_type.slug], request=request,
            )

        def list_context_link_or_func(view_instance, request, *args, **kwargs):
            resource_type = view_instance.get_resource_type()
            return reverse(
                "collections-json-ld", args=[resource_type.slug], request=request,
            )

    def get_resource_type(self):
        return get_resource_type_for(self.resource_type_name)

    def get_instance(self, request, slug: str):
        """
            Subclasses **MUST** override this method.
            Return the instance from the DB, used when updating,
            retrieving and deleting the instance.
        """
        raise NotImplementedError()

    def get_serializer(self, *args, **kwargs):
        kwargs["resource_type"] = self.get_resource_type()
        return super().get_serializer(*args, **kwargs)

    def create(self, request):
        """ Add a Resource."""
        raise NotImplementedError()

    def update(self, request, slug: str):
        """Update a Resource."""
        raise NotImplementedError()

    def destroy(self, request, slug: str):
        """Update a Resource."""
        raise NotImplementedError()

    def retrieve(self, request, slug: str):
        """Return the resource for the given resource type name and slug."""
        raise NotImplementedError()

    def list(self, request):
        """Return the list of resources for the given resource type name."""
        raise NotImplementedError()
