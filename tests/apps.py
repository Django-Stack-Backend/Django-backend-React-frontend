from django.apps import AppConfig

from scrud_django.scrud_signals import ScrudSignalProcessor


class TestsConfig(AppConfig):
    name = "tests"

    def ready(self):
        ScrudSignalProcessor()
