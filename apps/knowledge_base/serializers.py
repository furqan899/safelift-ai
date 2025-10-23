"""
Serializers for Knowledge Base entries.

Following Clean Code principles:
- Single responsibility
- Clear naming
- DRY (no duplication)
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import KnowledgeBaseEntry
from .utils import MAX_SEARCH_TOP_K

User = get_user_model()


class KnowledgeBaseEntrySerializer(serializers.ModelSerializer):
    """Complete serializer for Knowledge Base entries."""

    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    embedding_status_display = serializers.CharField(
        source='get_embedding_status_display',
        read_only=True
    )
    languages = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeBaseEntry
        fields = [
            'id',
            'issue_title_en',
            'solution_en',
            'issue_title_sv',
            'solution_sv',
            'category',
            'status',
            'status_display',
            'embedding_status',
            'embedding_status_display',
            'pinecone_vector_ids',
            'metadata',
            'tags',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
            'processed_at',
            'languages'
        ]
        read_only_fields = [
            'id',
            'embedding_status',
            'pinecone_vector_ids',
            'created_by',
            'created_at',
            'updated_at',
            'processed_at'
        ]

    def get_languages(self, obj) -> list:
        """Get list of available languages for this entry."""
        languages = []
        if obj.issue_title_en and obj.solution_en:
            languages.append('EN')
        if obj.issue_title_sv and obj.solution_sv:
            languages.append('SV')
        return languages


class KnowledgeBaseEntryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Knowledge Base entries."""

    class Meta:
        model = KnowledgeBaseEntry
        fields = [
            'id',
            'issue_title_en',
            'solution_en',
            'issue_title_sv',
            'solution_sv',
            'category',
            'tags',
            'metadata'
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'issue_title_en': {'required': False, 'allow_blank': True, 'allow_null': True},
            'solution_en': {'required': False, 'allow_blank': True, 'allow_null': True},
            'issue_title_sv': {'required': False, 'allow_blank': True, 'allow_null': True},
            'solution_sv': {'required': False, 'allow_blank': True, 'allow_null': True},
            'tags': {'required': False},
            'metadata': {'required': False}
        }

    def validate(self, data):
        """Validate that at least one complete language entry is provided."""
        issue_en = data.get('issue_title_en', '').strip() if data.get('issue_title_en') else ''
        solution_en = data.get('solution_en', '').strip() if data.get('solution_en') else ''
        issue_sv = data.get('issue_title_sv', '').strip() if data.get('issue_title_sv') else ''
        solution_sv = data.get('solution_sv', '').strip() if data.get('solution_sv') else ''
        
        has_english = bool(issue_en and solution_en)
        has_swedish = bool(issue_sv and solution_sv)
        
        if not has_english and not has_swedish:
            raise serializers.ValidationError(
                "At least one complete language entry (title and solution) is required."
            )
        
        # Validate partial entries
        if (issue_en and not solution_en) or (solution_en and not issue_en):
            raise serializers.ValidationError(
                "Both title and solution are required for English entry."
            )
        
        if (issue_sv and not solution_sv) or (solution_sv and not issue_sv):
            raise serializers.ValidationError(
                "Both title and solution are required for Swedish entry."
            )
        
        return data

    def create(self, validated_data):
        """Create a new Knowledge Base entry."""
        user = self.context['request'].user
        
        entry = KnowledgeBaseEntry.objects.create(
            created_by=user,
            **validated_data
        )
        
        return entry


class KnowledgeBaseEntryUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Knowledge Base entries."""

    class Meta:
        model = KnowledgeBaseEntry
        fields = [
            'issue_title_en',
            'solution_en',
            'issue_title_sv',
            'solution_sv',
            'category',
            'status',
            'tags',
            'metadata'
        ]
        extra_kwargs = {
            'issue_title_en': {'required': False, 'allow_blank': True, 'allow_null': True},
            'solution_en': {'required': False, 'allow_blank': True, 'allow_null': True},
            'issue_title_sv': {'required': False, 'allow_blank': True, 'allow_null': True},
            'solution_sv': {'required': False, 'allow_blank': True, 'allow_null': True},
            'tags': {'required': False},
            'metadata': {'required': False}
        }

    def validate(self, data):
        """Validate that at least one complete language entry is provided."""
        instance = self.instance
        
        # Get current or new values
        issue_en = (data.get('issue_title_en', instance.issue_title_en) or '').strip()
        solution_en = (data.get('solution_en', instance.solution_en) or '').strip()
        issue_sv = (data.get('issue_title_sv', instance.issue_title_sv) or '').strip()
        solution_sv = (data.get('solution_sv', instance.solution_sv) or '').strip()
        
        has_english = bool(issue_en and solution_en)
        has_swedish = bool(issue_sv and solution_sv)
        
        if not has_english and not has_swedish:
            raise serializers.ValidationError(
                "At least one complete language entry (title and solution) is required."
            )
        
        # Validate partial entries
        if (issue_en and not solution_en) or (solution_en and not issue_en):
            raise serializers.ValidationError(
                "Both title and solution are required for English entry."
            )
        
        if (issue_sv and not solution_sv) or (solution_sv and not issue_sv):
            raise serializers.ValidationError(
                "Both title and solution are required for Swedish entry."
            )
        
        return data


class KnowledgeBaseEntryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing Knowledge Base entries."""

    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    languages = serializers.SerializerMethodField()
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = KnowledgeBaseEntry
        fields = [
            'id',
            'issue_title_en',
            'issue_title_sv',
            'category',
            'status',
            'status_display',
            'embedding_status',
            'languages',
            'created_by_name',
            'created_at',
            'updated_at'
        ]

    def get_languages(self, obj) -> list:
        """Get list of available languages for this entry."""
        languages = []
        if obj.issue_title_en and obj.solution_en:
            languages.append('EN')
        if obj.issue_title_sv and obj.solution_sv:
            languages.append('SV')
        return languages


class KnowledgeBaseSearchSerializer(serializers.Serializer):
    """Serializer for search requests."""

    query = serializers.CharField(
        required=True,
        max_length=1000,
        help_text="Search query text"
    )
    language = serializers.ChoiceField(
        choices=['en', 'sv'],
        required=False,
        help_text="Filter by language (en/sv)"
    )
    category = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Filter by category"
    )
    top_k = serializers.IntegerField(
        default=5,
        min_value=1,
        max_value=MAX_SEARCH_TOP_K,
        help_text="Number of results to return"
    )
    include_content = serializers.BooleanField(
        default=True,
        help_text="Include full content in results"
    )
