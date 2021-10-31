import os
import sys

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--no-pkgroot",
        action="store_true",
        default=False,
        help="Remove package root directory from sys.path, ensuring that "
        "rest_framework is imported from the installed site-packages. "
        "Used for testing the distribution.",
    )


def pytest_configure(config):
    from django.conf import settings

    settings.configure(
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }  # noqa: E231
        },
        SITE_ID=1,
        SECRET_KEY="not very secret in tests",
        USE_I18N=True,
        USE_L10N=True,
        STATIC_URL="/static/",
        ROOT_URLCONF="tests.urls",
        TEMPLATE_LOADERS=(
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ),
        MIDDLEWARE=(
            "django.middleware.common.CommonMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ),
        INSTALLED_APPS=(
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.sites",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "django_jsonfield_backport",
            "haystack",
            "rest_framework",
            "rest_framework.authtoken",
            "scoped_rbac",
            "scrud_django",
            "tests",
            "reversion",
        ),
        PASSWORD_HASHERS=(
            "django.contrib.auth.hashers.SHA1PasswordHasher",
            "django.contrib.auth.hashers.PBKDF2PasswordHasher",
            "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
            "django.contrib.auth.hashers.BCryptPasswordHasher",
            "django.contrib.auth.hashers.MD5PasswordHasher",
            "django.contrib.auth.hashers.CryptPasswordHasher",
        ),
        REST_FRAMEWORK={
            "EXCEPTION_HANDLER": "scrud_django.exceptions.scrud_exception_handler",
            "DEFAULT_PERMISSION_CLASSES": [
                "scoped_rbac.permissions.IsAuthorized",
                # "rest_framework.permissions.IsAdminUser",
            ],
        },
        SCOPED_RBAC={
            "POLICY_FOR_UNAUTHENTICATED": "tests.rbac_defaults.policy_for_unauthenticated",  # noqa: E501
            "POLICY_FOR_STAFF": "tests.rbac_defaults.policy_for_staff",
        },
        SCRUD_WORKFLOW={
            "DEFAULT_WORKFLOW_POLICIES": "tests.workflow_defaults.workflow_policies",
        },
        HAYSTACK_CONNECTIONS={
            'default': {
                'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
                'PATH': os.path.join(os.path.dirname(__file__), 'whoosh_index'),
            },
        },
        HAYSTACK_SIGNAL_PROCESSOR='haystack.signals.RealtimeSignalProcessor',
        SCRUD_WORKFLOW_ACTIONS=["tests.workflow_actions.actions"],
    )

    if config.getoption("--no-pkgroot"):
        sys.path.pop(0)

        # import scoped_rbac before pytest re-adds the package root directory.
        import scrud_django  # noqa

        package_dir = os.path.join(os.getcwd(), "scrud_django")
        assert not scrud_django.__file__.startswith(package_dir)

    try:
        import django  # noqa

        django.setup()
    except AttributeError:
        pass


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Ensure that the partner-profiles resource type is properly initialized for all
    tests.
    """
    from tests import resource_types

    with django_db_blocker.unblock():
        resource_types.json_resource_types()
