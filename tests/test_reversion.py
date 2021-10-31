import pytest
from reversion.models import Version

from scrud_django.registration import ResourceRegistration

from .factories import fake_resource


@pytest.mark.django_db
@pytest.fixture
def resource_creator():
    new_resource = fake_resource()
    new_resource = ResourceRegistration.register(
        new_resource.content, new_resource.resource_type.slug
    )

    return new_resource


@pytest.mark.django_db
def test_reversion_create(resource_creator):
    versions = Version.objects.filter(object_id=resource_creator.pk).count()
    assert versions > 0


@pytest.mark.django_db
def test_version_update(resource_creator):
    created_resource = ResourceRegistration.update(
        resource_creator.content,
        resource_creator.resource_type.slug,
        resource_creator.pk,
    )
    versions = Version.objects.filter(object_id=created_resource.pk).count()
    assert versions >= 2
