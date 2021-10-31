from django.apps import AppConfig

from scrud_django.scrud_signals import ScrudSignalProcessor


class ScrudConfig(AppConfig):
    name = "scrud_django"

    def ready(self):
        from scoped_rbac.conf import register_operator

        from scrud_django.permissions import authorized_transitions

        register_operator("scrud_workflow", authorized_transitions)

        self.processor = ScrudSignalProcessor()
