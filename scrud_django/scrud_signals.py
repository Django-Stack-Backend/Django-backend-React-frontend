from django.dispatch import Signal

from .conf import workflow_actions

scrud_post_save = Signal()
scrud_post_delete = Signal()


class ScrudSignalProcessor:
    workflow_actions = {}
    post_save_literal = 'on_save'
    post_delete_literal = 'on_delete'
    resource_type_uri_literal = 'resource_type_uri'

    def __init__(self) -> None:
        scrud_post_save.connect(self.post_save_trigger)
        scrud_post_delete.connect(self.post_delete_trigger)
        self.workflow_actions = workflow_actions()

    def post_save_trigger(self, sender, **kwargs):
        action = self.determine_action(
            self.post_save_literal, kwargs.get(self.resource_type_uri_literal)
        )
        if action:
            action(sender, **kwargs)

    def post_delete_trigger(self, sender, **kwargs):
        action = self.determine_action(
            self.post_delete_literal, kwargs.get(self.resource_type_uri_literal)
        )
        if action:
            action(sender, **kwargs)

    def determine_action(self, post_literal, type_uri):
        actions = self.workflow_actions.get(type_uri, None)
        if actions is not None:
            if post_literal in actions:
                return actions[post_literal]
        return None
