import json
from datetime import timezone

from django.utils.http import http_date, quote_etag
from rest_framework.reverse import reverse

from scrud_django.headers import get_link_header_for


class SerializerMixin:
    def __init__(self, *args, **kwargs):
        self.resource_type = kwargs.pop("resource_type")
        super().__init__(*args, **kwargs)

    def to_representation(self, instance, envelope=False, context=None):
        if type(instance.content) is str:
            content = json.loads(instance.content)
        else:
            content = instance.content
        if not envelope:
            return content
        request = self._context["request"]
        last_modified = http_date(
            instance.modified_at.replace(tzinfo=timezone.utc).timestamp()
        )
        return {
            'href': reverse(
                self.resource_type.route_name_detail(),
                args=[instance.id],
                request=request,
            ),
            'last_modified': last_modified,
            'etag': quote_etag(instance.etag),
            'link': get_link_header_for(self.resource_type, request),
            'content': content,
        }

    def to_internal_value(self, data):
        return data

    def create(self, validated_data):
        """ Create and return instance """
        return NotImplementedError()

    def update(self, instance, validated_data):
        """ Update and return instance """
        return NotImplementedError()
