from django.db.models import Manager
from rest_framework import serializers

from scrud_django import models
from scrud_django.mixins.serializer_mixins import SerializerMixin
from scrud_django.models import Resource
from scrud_django.registration import ResourceRegistration
from scrud_django.validators import JsonValidator, WorkflowValidator


class EnvelopeSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        iterable = data.all() if isinstance(data, Manager) else data
        return [self.child.to_representation(item, envelope=True) for item in iterable]


class ResourceSerializer(SerializerMixin, serializers.Serializer):
    class Meta:
        model = models.Resource
        list_serializer_class = EnvelopeSerializer
        validators = [JsonValidator(), WorkflowValidator()]

    def create(self, validated_data):
        instance = Resource(content=validated_data, resource_type=self.resource_type)
        return ResourceRegistration.register_instance(instance)

    def update(self, instance, validated_data):
        return ResourceRegistration.update(
            content=validated_data,
            register_type=self.resource_type.slug,
            slug=instance.slug,
        )


class JSONSchemaSerializer(serializers.Serializer):
    """Serializer for JSON-Schema data."""

    class Meta:
        fields = ["$id", "$schema", "title", "description", "properties"]


class JSONLDSerializer(serializers.Serializer):
    """Serializer for JSON-LD data."""

    class Meta:
        fields = ["$id", "$schema", "title", "description", "properties"]
