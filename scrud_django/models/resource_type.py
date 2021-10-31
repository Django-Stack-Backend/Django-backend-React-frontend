"""
This will support queries, such as:
    GET /resource_type/schema?uri=http://schema.org/person
    GET /resource_type/context?uri=http://schema.org/person

"""
import reversion
from django.db import models
from django.utils.translation import gettext_lazy as _


@reversion.register()
class ResourceType(models.Model):
    type_uri = models.URLField()

    # only necessary if there is a collection endpoint associated
    # with this ResourceType
    slug = models.CharField(max_length=255, null=True)

    # require either schema or schema_uri
    schema = models.ForeignKey(
        'Resource',
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_('schema'),
        related_name='resource_type_schema',
    )
    schema_uri = models.URLField(null=True)

    # require either context or context_uri
    context = models.ForeignKey(
        'Resource',
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_('linked-data context'),
        related_name='resource_type_context',
    )
    context_uri = models.URLField(null=True)
    indexing_policy = models.ForeignKey(
        'Resource',
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_('indexing policy'),
        related_name='resource_type_indexing_policy',
    )
    modified_at = models.DateTimeField()
    etag = models.CharField(max_length=40)
    revision = models.CharField(max_length=40)
    uses_reversion = models.BooleanField(default=True)

    def route_name_list(self):
        return f"{self.slug}-list"

    def route_name_detail(self):
        return f"{self.slug}-detail"
