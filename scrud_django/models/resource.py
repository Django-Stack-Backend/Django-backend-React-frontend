"""
This will support queries, such as:
    GET /resource_type/schema?uri=http://schema.org/person
    GET /resource_type/context?uri=http://schema.org/person

"""
import reversion
from django.db import models

from scrud_django.mixins.resource_mixin import ResourceMixin
from scrud_django.models.resource_type import ResourceType


@reversion.register()
class Resource(ResourceMixin):
    resource_type = models.ForeignKey(
        ResourceType,
        on_delete=models.PROTECT,
        verbose_name='resource type',
        related_name='resource_type',
    )
