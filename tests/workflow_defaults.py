import importlib.resources
import json
from scrud_django.workflow import WorkflowPolicy


def workflow_policies():
  return {
    "tests://ToDo": read_workflow_policy("tests.static.todo_flow", "workflow.json")
  }


def read_workflow_policy(module, filename):
  text = importlib.resources.read_text("tests.static.todo_flow", "workflow.json")
  policy_json = json.loads(text)
  return WorkflowPolicy(policy_json)