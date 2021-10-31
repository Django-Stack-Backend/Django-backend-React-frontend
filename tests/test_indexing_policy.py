import pytest

from scrud_django.models import ResourceType


@pytest.mark.django_db
def test_partner_profile_indexing_policy_exists():
    indexing_policy_resource_type = ResourceType.objects.get(
        type_uri="http://api.openteams.com/json-ld/IndexingPolicy"
    )
    assert indexing_policy_resource_type is not None

    partner_profile_resource_type = ResourceType.objects.get(
        type_uri="tests://PartnerProfiles"
    )
    assert partner_profile_resource_type.indexing_policy is not None

    assert (
        partner_profile_resource_type.indexing_policy.resource_type
        == indexing_policy_resource_type
    )
