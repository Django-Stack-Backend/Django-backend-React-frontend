from datetime import timezone

from django.utils.http import http_date
from haystack import indexes
from jsonpath_ng import parse

from .models import Resource


class ResourceIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=False)
    type_uri = indexes.CharField(use_template=False)
    modified_at = indexes.CharField(use_template=False)
    etag = indexes.CharField(use_template=False)

    def get_model(self):
        return Resource

    def prepare(self, obj):
        self.prepared_data = super().prepare(obj)
        self.prepared_data["type_uri"] = obj.resource_type.type_uri
        self.prepared_data["modified_at"] = http_date(
            obj.modified_at.replace(tzinfo=timezone.utc).timestamp()
        )
        self.prepared_data["etag"] = obj.etag
        indexing_policy = self.get_indexing_policy(obj)
        text_policy = indexing_policy.get("text", None)
        # TODO in order to have an indexing policy per ResourceType in Haystack we'd
        # need to have a Model per ResourceType. We *can* figure that out, but, let's
        # figure out one thing at a time. For now, we'll index only the primary document
        # content using the indexing policy, leaving indexing of fields to a later date.
        # self.prepared_data.update({
        #     field: self.apply(policy, obj.content) for field, policy in
        #         indexing_policy.items()
        # })
        if text_policy:
            self.prepared_data["text"] = self.apply(text_policy, obj.content)
        else:
            self.prepared_data["text"] = ""
        return self.prepared_data

    def get_indexing_policy(self, obj):
        if obj.resource_type.indexing_policy is None:
            return {}
        return obj.resource_type.indexing_policy.content

    def apply(self, policy, content):
        ret = None
        if isinstance(policy, list):
            for p in policy:
                ret = self.concat_result(ret, self.apply(p, content))
        else:
            compiled_policy = parse(policy)
            for match in compiled_policy.find(content):
                ret = self.concat_result(ret, match.value)
        return ret

    def concat_result(self, original, addition):
        if original is None:
            return addition
        if original is not None and addition is None:
            return original
        return original + "\n" + addition
