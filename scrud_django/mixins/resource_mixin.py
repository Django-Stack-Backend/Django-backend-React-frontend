from typing import Dict, Tuple

from django.db import models
from django.utils.translation import gettext_lazy as _
from django_jsonfield_backport.models import JSONField

from scrud_django.conf import default_workflow_policies
from scrud_django.models.resource_type import ResourceType
from scrud_django.workflow import (
    TransitionData,
    WorkflowInvalidInitialStateError,
    WorkflowInvalidStateError,
    WorkflowPolicy,
    WorkflowTransitionError,
)

from ..scrud_signals import scrud_post_delete, scrud_post_save

workflow_policy_type_uri = "http://api.openteams.com/json-ld/WorkflowPolicy"


class ResourceMixin(models.Model):
    # The actual JSON content for this resource
    content = JSONField()
    resource_type = models.ForeignKey(
        ResourceType, on_delete=models.PROTECT, verbose_name=_('resource type'),
    )
    modified_at = models.DateTimeField()
    etag = models.CharField(max_length=40)

    @property
    def rbac_context(self):
        return self.content.get("rbac_context", None)

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ) -> None:
        transition_data = self.get_transition_data()
        action = 'CREATE' if self._state.adding else 'UPDATE'
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
        scrud_post_save.send(
            sender=self.__class__,
            instance=self,
            update_fields=update_fields,
            using=using,
            resource_type_uri=self.resource_type.type_uri,
            transition_data=transition_data,
            action=action,
        )

    def delete(self, using=None, keep_parents=False) -> Tuple[int, Dict[str, int]]:
        res = super().delete(using=using, keep_parents=keep_parents)
        scrud_post_delete.send(
            sender=self.__class__,
            instance=self,
            using=using,
            resource_type_uri=self.resource_type.type_uri,
            action='DELETE',
        )
        return res

    def get_transition_data(self):
        if self._state.adding:
            prior_data = None
        else:
            prior_version = self.__class__.objects.filter(pk=self.pk)
            prior_data = prior_version.first().content
        workflow = self.get_workflow_policy()
        if workflow is None:
            return None
        elif prior_data is None:
            return TransitionData(None, self.content, "__INITIALIZE__")
        try:
            return workflow.determine_transition(self.content, prior_data)
        except (
            WorkflowInvalidInitialStateError,
            WorkflowInvalidStateError,
            WorkflowTransitionError,
        ):
            """ Workflow validation shouldn't happen in here.
                hence we ignore the exceptions. """
            return None

    def get_workflow_policy(self):
        workflow = self.__class__.objects.filter(
            resource_type__type_uri=workflow_policy_type_uri,
            content__resource_type=self.resource_type.type_uri,
        )
        dflt_workflow_policies = default_workflow_policies()
        if workflow.exists() and self.rbac_context is None:
            return WorkflowPolicy(workflow.first().content)
        elif workflow.exists() and self.rbac_context:
            return WorkflowPolicy(
                workflow.filter(content__rbac_context=self.rbac_context).first().content
            )
        elif self.resource_type.type_uri in default_workflow_policies():
            return dflt_workflow_policies[self.resource_type.type_uri]
        return None

    class Meta:
        abstract = True
