from datetime import datetime
from uuid import uuid4

import factory
from django.contrib.auth.models import User

from scrud_django.models import Resource, ResourceType


def fake_url():
    return 'https://a{}.com'.format(uuid4().hex)


def fake_resource():
    resource_type = ResourceTypeFactory(schema=None, context=None)
    return ResourceFactory(resource_type=resource_type)


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: f'test_user_{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'test_password')
    is_staff = False

    class Meta:
        model = User


class ResourceTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ResourceType

    type_uri = factory.LazyFunction(fake_url)
    slug = factory.LazyFunction(lambda: uuid4().hex)

    schema = factory.LazyFunction(fake_resource)
    schema_uri = None

    context = factory.LazyFunction(fake_resource)
    context_uri = None

    modified_at = factory.LazyFunction(datetime.now)
    etag = factory.LazyFunction(lambda: uuid4().hex)
    uses_reversion = True


class ResourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Resource

    content = factory.LazyFunction(lambda: {'name': uuid4().hex})
    resource_type = factory.SubFactory(ResourceTypeFactory)
    modified_at = factory.LazyFunction(datetime.now)
    etag = factory.LazyFunction(lambda: uuid4().hex)
