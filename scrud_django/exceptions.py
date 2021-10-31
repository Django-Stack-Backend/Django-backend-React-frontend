from rest_framework.exceptions import APIException
from rest_framework.reverse import reverse
from rest_framework.views import exception_handler as drf_exception_handler


def scrud_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if isinstance(exc, ScrudException):
        response.data = exc.response_data(context)
        response.data["status"] = response.status_code
        try:
            request = context["request"]
            if request.accepted_renderer.format == "json":
                response.content_type = "application/problem+json"
        except AttributeError:
            pass
    return response


class ScrudException(APIException):
    def response_data(self, context):
        """Return RFC 7807 response data"""
        data = {}
        for property_name in ["type", "title", "detail", "instance"]:
            if hasattr(self, property_name):
                data[property_name] = getattr(self, property_name)
        return data


class JsonValidationError(ScrudException):
    status_code = 400
    default_detail = "Bad Request"

    def __init__(self, json_schema_exc):
        super().__init__()
        self.type = "https://api.openteams.com/http-problem/json-invalid"
        self.title = "JSON Validation Error"
        self.detail = json_schema_exc.message
        self.exc = json_schema_exc

    def response_data(self, context):
        data = super().response_data(context)
        data["name"] = self.exc.name
        data["value"] = self.exc.value
        data["definition"] = self.exc.definition
        data["rule"] = self.exc.rule
        data["rule_definition"] = self.exc.rule_definition
        return data


class WorkflowTransitionError(ScrudException):
    status_code = 400
    default_detail = "Bad Request"

    def __init__(self, policy, prior_state, proposed_state, message=None):
        super().__init__()
        self.type = "http://api.openteams.com/http-problem/workflow-transition-invalid"
        self.title = "Invalid workflow transition"
        self.detail = message if message is not None else policy
        self.policy = policy
        self.prior_state = prior_state
        self.proposed_state = proposed_state
        self.message = message if message is not None else self.title

    def response_data(self, context):
        data = super().response_data(context)
        # TODO make this work correctly
        # data["policy"] = reverse('workflow-policies', {"id": self.policy.id})
        data["policy"] = self.policy
        data["prior_state"] = self.prior_state
        data["proposed_state"] = self.proposed_state
        data["message"] = self.message
        return data


class WorkflowInvalidInitialStateError(WorkflowTransitionError):
    def __init__(self, policy, proposed_state):
        super().__init__(
            policy,
            None,
            proposed_state,
            message="The request is not a valid initial state.",
        )


class WorkflowInvalidStateError(WorkflowTransitionError):
    def __init__(self, policy):
        super().__init__(
            policy, None, None, message="The request does not match a valid state"
        )