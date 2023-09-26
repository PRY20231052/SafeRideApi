from rest_framework import serializers

class DirectionSerializer(serializers.Serializer):
    ending_action = serializers.CharField(max_length=30)
    street_name = serializers.CharField(max_length=100)
    covered_edges_indexes = serializers.ListField()
    covered_polyline_points_indexes = serializers.ListField()

    def create(self, validated_data):
        # is the same as Direction(**validated_data) for serializers withouth nested serializers
        return super().create(validated_data)