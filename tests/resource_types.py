import importlib.resources
from scrud_django import registration


def json_resource_types():
    """This is implemented as a function in the tests so that the json resource types
    may be recreated in `conftest.py`, otherwise they're wiped on each clean of the
    database!.
    """
    return [
        registration.json_resource_type(
            resource_type_uri="tests://PartnerProfiles",
            revision="2",
            slug="partner-profiles",
            schema_func=lambda: importlib.resources.read_text(
                "tests.static.partner_profile", "schema.json"
            ),
            context_func=lambda: importlib.resources.read_text(
                "tests.static.partner_profile", "ld.json"
            ),
            indexing_policy_func=lambda: importlib.resources.read_text(
                "tests.static.partner_profile", "indexing-policy.json"
            ),
        ),
        registration.json_resource_type(
            resource_type_uri="tests://ToDo",
            revision="1",
            slug="todos",
            schema_func=lambda: importlib.resources.read_text(
                "tests.static.todo_flow", "schema.json"
            ),
            context_func=lambda: importlib.resources.read_text(
                "tests.static.todo_flow", "ld.json"
            ),
        ),
    ]