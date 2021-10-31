from rest_framework.response import Response
from rest_framework.views import APIView


class ScrudfulView(APIView):
    def etag(self, request):
        raise NotImplementedError()

    def last_modified(self, request):
        raise NotImplementedError()

    def schema_url(self, request):
        raise NotImplementedError()

    def context_url(self, request):
        raise NotImplementedError()

    def schema_link_url(self, request):
        raise NotImplementedError()

    def schema_link_content_type(self, request):
        raise NotImplementedError()

    def context_link_url(self, request):
        raise NotImplementedError()

    def context_link_content_type(self, request):
        raise NotImplementedError()

    def context_link_rel(self, request):
        return "context"

    def do_get(self, request, format=None):
        raise NotImplementedError()

    def do_options(self, request, format=None):
        raise NotImplementedError()

    def context_link_content(self, request):
        context_link_url = self.context_link_url(request)
        if context_link_url:
            return (
                f"<{self.context_link_url(request)}>; "
                f"rel=\"{self.context_link_rel(request)}\"; "
                f"type=\"{self.context_link_content_type(request)}\""
            )
        else:
            return ""

    def schema_link_content(self, request):
        schema_link_url = self.schema_link_url(request)
        if schema_link_url:
            return (
                f"<{self.schema_link_url(request)}>; "
                "rel=\"describedBy\"; "
                f"type=\"{self.schema_link_content_type(request)}\""
            )
        else:
            return ""

    def set_link_header(self, request, response):
        link_content = self.schema_link_content(request)
        context_link_content = self.context_link_content(request)
        if link_content and context_link_content:
            link_content = f"{link_content}, {context_link_content}"
        elif context_link_content:
            link_content = context_link_content
        if link_content:
            response["Link"] = link_content

    def get(self, request, format=None):
        response = self.do_get(request, format=format)
        response['ETag'] = f"\"{self.etag(request)}\""
        response['Last-Modified'] = self.last_modified(request)
        self.set_link_header(request, response)
        return response

    def options(self, request, format=None):
        response = self.do_options(request, format=None)
        response['Allow'] = "GET, HEAD"
        response['ETag'] = f"\"{self.etag(request)}\""
        response['Last-Modified'] = self.last_modified(request)
        response['Link'] = (
            "</json-schema/http-schema>; rel=\"describedBy\"; "
            "type=\"application/json\", "
            "</json-ld/http-schema>; rel=\"http://www.w3.org/ns/json-ld#context\"; "  # noqa
            "type=\"application/ld+json\""
        )
        return response


class ScrudfulJsonView(ScrudfulView):
    def schema_link_content_type(self, request):
        return "application/json"

    def context_link_rel(self, request):
        return "http://www.w3.org/ns/json-ld#context"

    def context_link_content_type(self, request):
        return "application/ld+json"


class ExamplePartnerProfile(ScrudfulJsonView):
    def etag(self, request):
        return "1"

    def last_modified(self, request):
        return "Thu, 20 Aug 2020 00:00:00 GMT"

    def schema_link_url(self, request):
        return "/json-schema/PartnerProfile"

    def context_link_url(self, request):
        return "/json-ld/PartnerProfile"

    def do_get(self, request, format=None):
        return Response(
            {
                "name": "Semantics and CRUD, LLC",
                "display_name": "Semantics and CRUD",
                "slug": "semantics-crud",
                "logo": "http://backend.openteams.com/partners/semantics-crud/media/logo.png",  # noqa
                "id": "some-uuid",
            }
        )

    def do_options(self, request, format=None):
        return Response(
            {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "context": "/json-ld/PartnerProfile",
                                    "schema": "/json-schema/PartnerProfile",
                                },
                            },
                        },
                    },
                },
            }
        )


class PartnerProfileSchema(ScrudfulJsonView):
    def etag(self, request):
        return "1"

    def last_modified(self, request):
        return "Thu, 20 Aug 2020 00:00:00 GMT"

    def schema_link_url(self, request):
        return "https://json-schema.org/draft-06/schema"

    def context_link_url(self, request):
        return None

    def do_get(self, request, format=None):
        return Response(
            {
                "$id": "https://api.openteams.com/json-schema/PartnerProfile",
                "$schema": "http://json-schema.org/draft-06/schema",
                "title": "Partner Profile",
                "description": "A resource detailing an OpenTeams Partner.",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The legal name of the Partner business entity.",  # noqa
                    },
                    "display_name": {
                        "type": "string",
                        "description": "The name to display when referencing the Partner.",  # noqa
                    },
                    "slug": {
                        "type": "string",
                        "description": "Suggested short name to use in URLs.",
                    },
                    "logo": {
                        "type": "string",
                        "format": "uri",
                        "description": "URL of a logo to display for the Partner.",  # noqa
                    },
                    "id": {
                        "type": "string",
                        "description": "The system identifier for the Partner Profile resource.",  # noqa
                    },
                },
            }
        )

    def do_options(self, request, format=None):
        return Response(
            {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "context": "https://json-schema.org/draft-06/schema",  # noqa
                                },
                            },
                        },
                    },
                },
            }
        )


class PartnerProfileContext(ScrudfulJsonView):
    def etag(self, request):
        return "1"

    def last_modified(self, request):
        return "Thu, 20 Aug 2020 00:00:00 GMT"

    def schema_link_url(self, request):
        return None

    def context_link_url(self, request):
        return None

    def do_get(self, request, format=None):
        return Response(
            {
                "schema": "http://schema.org/",
                "openteams": "http://api.openteams.com/json-ld/",
                "@type": "schema:Organization",
                "name": {"@id": "schema:legalName"},
                "display_name": {"@id": "schema:name"},
                "slug": {"@id": "schema:identifier"},
                "logo": {"@id": "schema:logo"},
                "id": {"@id": "rdfs:id"},
            }
        )

    def do_options(self, request, format=None):
        return Response(
            {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {"application/json": {}},
                        },
                    },
                },
            }
        )
