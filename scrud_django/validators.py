import fastjsonschema

from scoped_rbac.permissions import http_action_iri_for, policy_for, DEFAULT_CONTEXT
from scoped_rbac.policy import Permission
from scrud_django.conf import default_workflow_policies
from scrud_django.exceptions import JsonValidationError, WorkflowTransitionError
from scrud_django.models import Resource, ResourceType
from scrud_django.registration import workflow_policy_resource_type
from scrud_django.permissions import TransitionCheck
from scrud_django.workflow import TransitionData, WorkflowPolicy


class ValidatorEntry:
    def __init__(self, resource_type: ResourceType, validate: callable):
        self.type_uri = resource_type.type_uri
        self.revision = resource_type.revision
        self.etag = resource_type.schema.etag
        self.modified_at = resource_type.schema.modified_at
        self.validate = validate

    def matches(self, resource_type: ResourceType):
        return (
            self.type_uri == resource_type.type_uri
            and self.revision == resource_type.revision
            and self.etag == resource_type.schema.etag
            and self.modified_at == resource_type.schema.modified_at
        )


class JsonValidator:
    requires_context = True

    def __init__(self):
        self.validators = {}

    def __call__(self, data, context):
        validate = self.validator_for(context.resource_type)
        data = validate(data)
        return data

    def is_json_schema(self, schema):
        return schema is not None and schema.resource_type.type_uri in [
            "http://json-schema.org/draft-04/schema",
            "http://json-schema.org/draft-06/schema",
            "http://json-schema.org/draft-07/schema",
        ]

    def validator_for(self, resource_type):
        schema = resource_type.schema
        if not self.is_json_schema(schema):
            return lambda r: r
        validator = self.validators.get(resource_type.type_uri, None)
        if validator is None or not validator.matches(resource_type):
            try:
                content = schema.content
                if "$id" in content:
                    del content["$id"]
                validation_func = fastjsonschema.compile(content)
            except Exception as e:
                import logging

                logging.error(e)
                return lambda r: r

            def validate(content, handlers={}, formats={}):
                try:
                    return validation_func(content)
                except fastjsonschema.JsonSchemaException as e:
                    raise JsonValidationError(e)

            validator = ValidatorEntry(resource_type, validate)
            self.validators[resource_type.type_uri] = validator
        return validator.validate


class WorkflowValidator:
    requires_context = True

    def __init__(self):
        self.default_policies = default_workflow_policies()
        self.cached_policies = {}

    def __call__(self, data, context):
        resource_type = context.resource_type
        policies = Resource.objects.filter(
            resource_type=workflow_policy_resource_type(),
            content__resource_type=resource_type.type_uri,
        )
        # TODO policy should be based on rbac_context per resource_type!!
        if policies.exists():
            for policy in policies.all():
                workflow_policy = self.workflow_policies.get(
                    (policy.id, policy.version), None
                )
                if workflow_policy is None:
                    workflow_policy = WorkflowPolicy(policy.content)
                    self.workflow_policies[
                        (policy.id, policy.version)
                    ] = workflow_policy
                self.apply(workflow_policy, data, context)
        elif (
            data.get("rbac_context", None) is None
            and resource_type.type_uri in self.default_policies
        ):
            workflow_policy = self.default_policies[resource_type.type_uri]
            self.apply(workflow_policy, data, context)
        return data

    def apply(self, workflow_policy, data, context):
        instance = context.instance
        if instance is None:
            workflow_policy.validate_initial_state(data)
            transition_data = TransitionData(None, data, "__INITIALIZE__")
        else:
            transition_data = workflow_policy.determine_transition(data, instance.content)
        request = context.context["request"]
        permissions_policy = policy_for(request)
        permission = Permission(
            http_action_iri_for(request), context.resource_type.type_uri
        )
        if not permissions_policy.should_allow(
            permission,
            data.get("rbac_context", DEFAULT_CONTEXT),
            resource=TransitionCheck(transition_data.transition),
        ):
            raise WorkflowTransitionError(
                workflow_policy.policy,
                transition_data.prior_state,
                transition_data.proposed_state,
                message="The user isn't authorized to perform this state transition on this resource.",
            )
