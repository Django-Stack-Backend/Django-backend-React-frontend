from dataclasses import dataclass
from scrud_django.exceptions import WorkflowTransitionError


@dataclass
class TransitionCheck:
    transition: str


def authorized_transitions(resource, configuration):
    """This permissions Operator function always returns `True`. It's a placeholder
    to enable the `WorkflowValidator` to instead look to see if there is a registered
    policy that dictates the authorized transitions. Otherwise, the workflow
    validation would run twice.
    
    To use this `scoped_rbac.policy.Operator`, define an operator condition that
    specifies the `allowed_transitions` property. Here's an example: ```json {
    "condition": "operator", "allowed_transitions": ["start"] }
    ```

    The name for the initial transition is `__INITIALIZE__`
    """
    if isinstance(resource, TransitionCheck):
        if resource.transition in configuration["authorized_transitions"]:
            return True
        else:
          return False
    return True
