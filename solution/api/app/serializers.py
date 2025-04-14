from collections import OrderedDict
from rest_framework import serializers


class ClearNullMixin(serializers.Serializer):
    def to_representation(self, instance):
        result = super().to_representation(instance)
        return self._remove_nulls(result)

    def _remove_nulls(self, data):
        if isinstance(data, dict):
            return OrderedDict(
                (k, self._remove_nulls(v)) for k, v in data.items() if v is not None
            )
        elif isinstance(data, list):
            return [self._remove_nulls(item) for item in data if item is not None]
        return data
