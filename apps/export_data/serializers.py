from rest_framework import serializers
from .models import Export


class ExportListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for export list view."""

    created_by_name = serializers.CharField(
        source="created_by.username",
        read_only=True,
    )
    data_types_display = serializers.SerializerMethodField()
    created_at_formatted = serializers.DateTimeField(
        source="created_at",
        read_only=True,
        format="%b %d, %Y at %H:%M",
    )

    class Meta:
        model = Export
        fields = [
            "id",
            "data_types",
            "data_types_display",
            "format",
            "status",
            "progress_percentage",
            "created_by_name",
            "created_at",
            "created_at_formatted",
            "file_size",
            "error_message",
        ]
        read_only_fields = fields

    def get_data_types_display(self, obj) -> str:
        """Format data types for display."""
        if not obj.data_types:
            return ""
        type_labels = []
        for dt in obj.data_types:
            label = dict(Export.DataType.choices).get(dt, dt)
            type_labels.append(label)
        return ", ".join(type_labels)


class ExportDetailSerializer(serializers.ModelSerializer):
    """Full serializer for export detail view."""

    created_by_name = serializers.CharField(
        source="created_by.username",
        read_only=True,
    )
    data_types_display = serializers.SerializerMethodField()
    format_display = serializers.CharField(
        source="get_format_display",
        read_only=True,
    )
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )
    created_at_formatted = serializers.DateTimeField(
        source="created_at",
        read_only=True,
        format="%Y-%m-%d %H:%M:%S",
    )
    completed_at_formatted = serializers.DateTimeField(
        source="completed_at",
        read_only=True,
        format="%Y-%m-%d %H:%M:%S",
    )

    class Meta:
        model = Export
        fields = [
            "id",
            "data_types",
            "data_types_display",
            "format",
            "format_display",
            "date_range_days",
            "include_personal_data",
            "status",
            "status_display",
            "progress_percentage",
            "file_path",
            "file_size",
            "error_message",
            "created_by_name",
            "created_at",
            "created_at_formatted",
            "updated_at",
            "completed_at",
            "completed_at_formatted",
        ]
        read_only_fields = fields

    def get_data_types_display(self, obj) -> str:
        if not obj.data_types:
            return ""
        type_labels = []
        for dt in obj.data_types:
            label = dict(Export.DataType.choices).get(dt, dt)
            type_labels.append(label)
        return ", ".join(type_labels)


class ExportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new export jobs."""

    class Meta:
        model = Export
        fields = [
            "data_types",
            "format",
            "date_range_days",
            "include_personal_data",
        ]

    def validate_data_types(self, value):
        """Ensure data_types is a non-empty list."""
        if not value or not isinstance(value, list):
            raise serializers.ValidationError("data_types must be a non-empty list")
        valid_types = [dt[0] for dt in Export.DataType.choices]
        for dt in value:
            if dt not in valid_types:
                raise serializers.ValidationError(f"Invalid data type: {dt}")
        return value

    def validate_date_range_days(self, value):
        """Ensure date_range_days is reasonable."""
        if value < 1 or value > 365:
            raise serializers.ValidationError(
                "date_range_days must be between 1 and 365"
            )
        return value
