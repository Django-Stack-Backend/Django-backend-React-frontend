from datetime import timezone
from functools import partial, update_wrapper

from django.utils.cache import get_conditional_response
from django.utils.http import http_date, quote_etag
from rest_framework import status
from rest_framework.metadata import BaseMetadata
from rest_framework.response import Response
from rest_framework.views import APIView

from scrud_django import __version__
from scrud_django.utils import get_string_or_evaluate, link_content


class ScrudfulViewFunc:
    def __init__(
        self,
        view_method,
        view_is_class_method=True,
        etag_func=None,
        last_modified_func=None,
        schema_link_or_func=None,
        schema_rel_or_func=None,
        schema_type_or_func=None,
        context_link_or_func=None,
        context_rel_or_func=None,
        context_type_or_func=None,
        http_schema_or_func=None,
    ):
        self.view_is_class_method = view_is_class_method
        self.view_method = view_method
        self.etag_func = etag_func
        self.last_modified_func = last_modified_func
        self.schema_link_or_func = schema_link_or_func
        self.schema_rel_or_func = schema_rel_or_func
        self.schema_type_or_func = schema_type_or_func
        self.context_link_or_func = context_link_or_func
        self.context_rel_or_func = context_rel_or_func
        self.context_type_or_func = context_type_or_func
        self.http_schema_or_func = http_schema_or_func
        update_wrapper(self, self.view_method)

    def __get__(self, obj, objtype):
        return partial(self.__call__, obj)

    def __call__(self, *args, **kwargs):
        if self.view_is_class_method:
            request = args[1]
        else:
            request = args[0]
        if request.method in ("PUT", "DELETE"):
            missing_required_headers = []
            if self.etag_func and not request.META.get("HTTP_IF_MATCH"):
                missing_required_headers.append("If-Match")
            if self.last_modified_func and not request.META.get(
                "HTTP_IF_UNMODIFIED_SINCE"
            ):
                missing_required_headers.append("If-Unmodified-Since")
            if missing_required_headers:
                # TODO Define standard error json
                response = Response(
                    {"missing-required-headers": missing_required_headers}, status=400,
                )
                return response

        # Compute values (if any) for the requested resource.
        def get_last_modified():
            if self.last_modified_func:
                last_modified = self.last_modified_func(*args, **kwargs)
                if last_modified:
                    return http_date(
                        last_modified.replace(tzinfo=timezone.utc).timestamp()
                    )
            return None

        etag = None
        last_modified = None
        if request.method not in ("POST", "OPTIONS"):
            if self.etag_func:
                etag = self.etag_func(*args, **kwargs)
                etag = etag + __version__ if etag else None
            etag = quote_etag(etag) if etag else None
            last_modified = get_last_modified()
        else:
            etag = None
            last_modified = None
        response = get_conditional_response(
            request, etag=etag, last_modified=last_modified
        )
        if response is None:
            response = self.view_method(*args, **kwargs)
            schema_link = self.schema_link_header(*args, **kwargs) or ""
            context_link = self.context_link_header(*args, **kwargs) or ""
            join_links = ", " if schema_link and context_link else ""
            link_content = schema_link + join_links + context_link
            if etag:
                response["ETag"] = etag
            if last_modified:
                response["Last-Modified"] = last_modified
            if link_content:
                response["Link"] = link_content
            self.add_expose_headers(response)
        return response

    def add_expose_headers(self, response):
        """If the Link and/or Location header are provided on the response add the
        'Access-Control-Expose-Headers` header to expose them over CORS requests.
        """
        expose_headers = ""
        if "Link" in response:
            expose_headers = "Link"
        if "Location" in response:
            if expose_headers:
                expose_headers = expose_headers + ", "
            expose_headers = expose_headers + "Location"
        if expose_headers:
            response["Access-Control-Expose-Headers"] = expose_headers

    def schema_link(self, *args, **kwargs):
        return get_string_or_evaluate(self.schema_link_or_func, *args, **kwargs)

    def schema_link_header(self, *args, **kwargs):
        link = self.schema_link(*args, **kwargs)
        if link:
            link_rel = (
                get_string_or_evaluate(self.schema_rel_or_func, *args, **kwargs,)
                or "describedBy"
            )
            link_type = (
                get_string_or_evaluate(self.schema_type_or_func, *args, **kwargs,)
                or "application/json"
            )
            return link_content(link, link_rel, link_type)
        return None

    def context_link(self, *args, **kwargs):
        return get_string_or_evaluate(self.context_link_or_func, *args, **kwargs)

    def context_link_header(self, *args, **kwargs):
        link = self.context_link(*args, **kwargs)
        if link:
            link_rel = (
                get_string_or_evaluate(self.context_rel_or_func, *args, **kwargs,)
                or "http://www.w3.org/ns/json-ld#context"
            )
            link_type = (
                get_string_or_evaluate(self.context_type_or_func, *args, **kwargs,)
                or "application/ld+json"
            )
            return link_content(link, link_rel, link_type)
        return None


def scrudful(
    etag_func=None,
    last_modified_func=None,
    schema_link_or_func=None,
    schema_rel_or_func=None,
    schema_type_or_func=None,
    context_link_or_func=None,
    context_rel_or_func=None,
    context_type_or_func=None,
    http_schema_or_func=None,
):
    """Decorator to make a view method SCRUDful"""
    # TODO what about 400 Bad Request context and schema?
    def decorator(view_method):
        return ScrudfulViewFunc(
            view_method,
            etag_func=etag_func,
            last_modified_func=last_modified_func,
            schema_link_or_func=schema_link_or_func,
            schema_rel_or_func=schema_rel_or_func,
            schema_type_or_func=schema_type_or_func,
            context_link_or_func=context_link_or_func,
            context_rel_or_func=schema_rel_or_func,
            context_type_or_func=schema_type_or_func,
            http_schema_or_func=http_schema_or_func,
        )

    return decorator


def scrudful_api_view(
    etag_func=None,
    last_modified_func=None,
    schema_link_or_func=None,
    schema_rel_or_func=None,
    schema_type_or_func=None,
    context_link_or_func=None,
    context_rel_or_func=None,
    context_type_or_func=None,
    http_schema_or_func=['GET'],
):
    def decorator(view_method, *args, **kwargs):

        http_method_names = http_schema_or_func
        allowed_methods = set(http_method_names) | {'options'}

        cls_attr = {
            '__doc__': view_method.__doc__,
            'metadata_class': ScrudfulAPIViewMetadata,
        }

        handler = ScrudfulViewFunc(
            lambda self, *args, **kwargs: view_method(*args, **kwargs),
            etag_func=etag_func,
            last_modified_func=last_modified_func,
            schema_link_or_func=schema_link_or_func,
            schema_rel_or_func=schema_rel_or_func,
            schema_type_or_func=schema_type_or_func,
            context_link_or_func=context_link_or_func,
            context_rel_or_func=context_rel_or_func,
            context_type_or_func=context_type_or_func,
        )

        for method in http_method_names:
            cls_attr[method.lower()] = handler

        ScrudAPIView = type('ScrudAPIView', (APIView,), cls_attr)

        ScrudAPIView.http_method_names = [method.lower() for method in allowed_methods]

        ScrudAPIView.__name__ = view_method.__name__
        ScrudAPIView.__module__ = view_method.__module__

        ScrudAPIView.permission_classes = getattr(
            view_method, 'permission_classes', APIView.permission_classes
        )
        ScrudAPIView.schema = getattr(view_method, 'schema', APIView.schema)
        ScrudAPIView.schema_link_or_func = schema_link_or_func
        ScrudAPIView.context_link_or_func = context_link_or_func

        # ScrudAPIView.options = options

        new_view_method = ScrudAPIView.as_view()

        return new_view_method

    return decorator


class ScrudfulMetadata(BaseMetadata):
    def determine_metadata(self, request, view, *args, **kwargs):
        if len(args) > 0 or len(kwargs) > 0:  # this is a detail request
            return self.determine_metadata_for_detail(request, view)
        return self.determine_metadata_for_list(request, view)

    def determine_metadata_for_detail(self, request, view):
        metadata = dict()
        metadata.update(
            {
                key: value
                for key, value in {
                    "get": self.determine_metadata_for_get(request, view, "retrieve"),
                    "put": self.determine_metadata_for_put(request, view),
                    "delete": self.determine_metadata_for_delete(request, view),
                }.items()
                if value is not None
            }
        )
        return metadata

    def determine_metadata_for_list(self, request, view):
        metadata = dict()
        metadata.update(
            {
                key: value
                for key, value in {
                    "post": self.determine_metadata_for_post(request, view),
                    "get": self.determine_metadata_for_get(request, view, "list"),
                }.items()
                if value is not None
            }
        )
        return metadata

    def get_method(self, view, name):
        method_partial = getattr(view, name, None)
        if method_partial:
            return method_partial.func.__self__
        return None

    def determine_metadata_for_post(self, request, view, name="create"):
        create_method = self.get_method(view, name)
        if create_method is None:
            return None
        schema_link = create_method.schema_link(view, request)
        context_link = create_method.context_link(view, request)
        request_body = {
            "description": "The content for the resource to be created.",
            "required": True,
        }
        if schema_link or context_link:
            json_content = {}
            if schema_link:
                json_content["schema"] = schema_link
            if context_link:
                json_content["context"] = context_link
            request_body["content"] = {
                "application/json": json_content,
            }
        metadata = {
            "requestBody": request_body,
            "responses": {"201": {"description": "CREATED"}},
        }
        return metadata

    def determine_metadata_for_get(self, request, view, name):
        list_method = self.get_method(view, name)
        if list_method is None:
            return
        schema_link = list_method.schema_link(view, request)
        context_link = list_method.context_link(view, request)
        json_content = None
        if schema_link or context_link:
            json_content = {}
            if schema_link:
                json_content["schema"] = schema_link
            if context_link:
                json_content["context"] = context_link
        responses = {
            "200": {"description": "OK"},
        }
        if json_content:
            responses["200"]["content"] = {
                "application/json": json_content,
            }
        return {
            "responses": responses,
        }

    def required_conditional_headers(self, method):
        supports_etag = method.etag_func is not None
        supports_last_modified = method.last_modified_func is not None
        parameters = None
        if supports_etag or supports_last_modified:
            parameters = []
            if supports_etag:
                parameters.append(
                    {
                        "in": "header",
                        "name": "If-Match",
                        "schema": {"type": "string"},
                        "required": True,
                    }
                )
            if supports_last_modified:
                parameters.append(
                    {
                        "in": "header",
                        "name": "If-Unmodified-Since",
                        "schema": {"type": "string"},
                        "required": True,
                    }
                )
        return parameters

    def determine_metadata_for_put(self, request, view, name="update"):
        update_method = self.get_method(view, name)
        if update_method is None:
            return
        schema_link = update_method.schema_link(view, request)
        context_link = update_method.context_link(view, request)
        request_body = {
            "description": "The content for the resource to be created.",
            "required": True,
        }
        if schema_link or context_link:
            json_content = {}
            if schema_link:
                json_content["schema"] = schema_link
            if context_link:
                json_content["context"] = context_link
            request_body["content"] = {
                "application/json": json_content,
            }
        metadata = {
            "requestBody": request_body,
            "responses": {"200": {"description": "OK"}},
        }
        parameters = self.required_conditional_headers(update_method)
        if parameters:
            metadata["parameters"] = parameters
        return metadata

    def determine_metadata_for_delete(self, request, view, name="destroy"):
        delete_method = self.get_method(view, name)
        if delete_method is None:
            return None
        metadata = {
            "responses": {"200": {"description": "OK"}},
        }
        parameters = self.required_conditional_headers(delete_method)
        if parameters:
            metadata["parameters"] = parameters
        return metadata


class ScrudfulAPIViewMetadata(ScrudfulMetadata):
    def determine_metadata(self, request, view, *args, **kwargs):
        metadata = dict()
        metadata.update(
            {
                key: value
                for key, value in {
                    "get": self.determine_metadata_for_get(request, view, "get"),
                    "post": self.determine_metadata_for_post(request, view, "post"),
                    "put": self.determine_metadata_for_put(request, view, "put"),
                    "delete": self.determine_metadata_for_delete(
                        request, view, "delete"
                    ),
                }.items()
                if value is not None
            }
        )
        return metadata


def options(view_instance, request, *args, **kwargs):
    data = ScrudfulMetadata().determine_metadata(
        request, view_instance, *args, **kwargs
    )
    return Response(data, status=status.HTTP_200_OK)


def scrudful_viewset(cls):
    setattr(cls, "options", options)
    meta = getattr(cls, "Meta", None)
    etag_func = getattr(meta, "etag_func", None)
    last_modified_func = getattr(meta, "last_modified_func", None)
    schema_link_or_func = getattr(meta, "schema_link_or_func", None)
    schema_rel_or_func = getattr(meta, "schema_rel_or_func", None)
    schema_type_or_func = getattr(meta, "schema_type_or_func", None)
    context_link_or_func = getattr(meta, "context_link_or_func", None)
    context_rel_or_func = getattr(meta, "context_rel_or_func", None)
    context_type_or_func = getattr(meta, "context_type_or_func", None)
    extra_view_methods = getattr(meta, "extra_view_methods", [])
    scrudful_item = scrudful(
        etag_func=etag_func,
        last_modified_func=last_modified_func,
        schema_link_or_func=schema_link_or_func,
        schema_rel_or_func=schema_rel_or_func,
        schema_type_or_func=schema_type_or_func,
        context_link_or_func=context_link_or_func,
        context_rel_or_func=context_rel_or_func,
        context_type_or_func=context_type_or_func,
    )
    view_methods = ["create", "retrieve", "update", "destroy"]
    view_methods.extend(extra_view_methods)
    for method_name in view_methods:
        method = getattr(cls, method_name, None)
        setattr(cls, method_name, scrudful_item(method))
    if hasattr(cls, "list"):
        scrudful_list = scrudful(
            etag_func=getattr(meta, "list_etag_func", None),
            last_modified_func=getattr(meta, "list_last_modified_func", None),
            schema_link_or_func=getattr(meta, "list_schema_link_or_func", None),
            schema_rel_or_func=getattr(meta, "list_schema_rel_or_func", None),
            schema_type_or_func=getattr(meta, "list_schema_type_or_func", None),
            context_link_or_func=getattr(meta, "list_context_link_or_func", None),
            context_rel_or_func=getattr(meta, "list_context_rel_or_func", None),
            context_type_or_func=getattr(meta, "list_context_type_or_func", None),
        )
        list_method = getattr(cls, "list")
        setattr(cls, "list", scrudful_list(list_method))
    return cls
