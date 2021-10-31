import pytest

from scrud_django.exceptions import (
    WorkflowInvalidInitialStateError,
    WorkflowInvalidStateError,
    WorkflowTransitionError,
)
from scrud_django.workflow import WorkflowPolicy

workflow_policy = WorkflowPolicy(
    {
        'rbac_context': 'test',
        'resource_type': 'test',
        'initial_states': {'start': 'status == "START"'},
        'states': {
            'middle': 'status == "MIDDLE"',
            'end': 'status == "END"',
            'unreachable': 'status == "UNREACHABLE"',
        },
        'transitions': {
            'move to middle': {'from': 'start', 'to': 'middle'},
            'move to end': {'from': ['start', 'middle'], 'to': 'end'},
        },
        'restrict_update': ['start', 'end'],
    }
)


start = {"status": "START"}
middle = {"status": "MIDDLE"}
end = {"status": "END"}
unreachable = {"status": "UNREACHABLE"}


def test_invalid_initial_state():
    with pytest.raises(WorkflowInvalidInitialStateError):
        workflow_policy.validate({"status": "Not a valid initial status"})


def test_valid_initial_state():
    assert workflow_policy.validate(start) == start


def test_invalid_state():
    with pytest.raises(WorkflowInvalidStateError):
        workflow_policy.validate({"bogus": "not a valid state!"}, start)


@pytest.mark.parametrize(
    "proposed_state, prior_state",
    [
        # (start, start),   # reflexive transitions must be explicit
        (start, middle),
        (start, end),
        (middle, end),
        (unreachable, start),
        (unreachable, middle),
        (unreachable, end),
    ],
)
def test_invalid_transition(proposed_state, prior_state):
    with pytest.raises(WorkflowTransitionError):
        workflow_policy.validate(proposed_state, prior_state)


@pytest.mark.parametrize(
    "proposed_state, prior_state", [(middle, start), (end, start), (end, middle)]
)
def test_valid_transition(proposed_state, prior_state):
    assert workflow_policy.validate(proposed_state, prior_state) == proposed_state


@pytest.mark.parametrize("proposed_state, prior_state", [(middle, middle)])
def test_same_state_transition(proposed_state, prior_state):
    assert workflow_policy.validate(proposed_state, prior_state) == proposed_state


@pytest.mark.parametrize("proposed_state, prior_state", [(start, start), (end, end)])
def test_same_state_update_restricted(proposed_state, prior_state):
    with pytest.raises(WorkflowTransitionError):
        workflow_policy.validate(proposed_state, prior_state)
