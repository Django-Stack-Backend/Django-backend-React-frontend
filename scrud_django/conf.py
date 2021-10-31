from django.conf import settings
from django.utils.module_loading import import_string
from rest_framework.settings import import_from_string

DEFAULTS = {"DEFAULT_WORKFLOW_POLICIES": {}}


def workflow_policy_settings():
    return getattr(settings, "SCRUD_WORKFLOW", dict())


def import_policy_or_func(setting):
    default = DEFAULTS[setting]
    policy_or_func = workflow_policy_settings().get(setting, default)
    if isinstance(policy_or_func, str):
        policy_or_func = import_from_string(policy_or_func, setting)
        if callable(policy_or_func):
            policy_or_func = policy_or_func()
    return policy_or_func


def default_workflow_policies():
    return import_policy_or_func("DEFAULT_WORKFLOW_POLICIES")


def workflow_action_settings():
    return getattr(settings, "SCRUD_WORKFLOW_ACTIONS", [])


def workflow_actions():
    all_actions = {}
    actions_strings: list = workflow_action_settings()
    if isinstance(actions_strings, list):
        for a_string in actions_strings:
            actions_by_type_uri: dict = import_string(a_string)
            for type_uri in list(actions_by_type_uri.keys()):
                all_actions[type_uri] = actions_by_type_uri.get(type_uri, None)
        return all_actions
