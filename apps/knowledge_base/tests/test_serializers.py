"""
Tests for KnowledgeBase serializers.
"""
from django.test import TestCase
from apps.knowledge_base.models import KnowledgeBaseEntry
from apps.knowledge_base.serializers import (
    KnowledgeBaseEntrySerializer,
    KnowledgeBaseEntryCreateSerializer
)
from apps.users.models import User


class KnowledgeBaseEntrySerializerTest(TestCase):
    """Test cases for KnowledgeBaseEntrySerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='pass123'
        )

    def test_valid_serialization(self):
        """Test serializing knowledge base entry."""
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_en='Test Issue',
            solution_en='Test Solution',
            category='Hydraulics',
            created_by=self.user
        )
        
        serializer = KnowledgeBaseEntrySerializer(instance=entry)
        data = serializer.data
        
        self.assertEqual(data['issue_title_en'], 'Test Issue')
        self.assertEqual(data['solution_en'], 'Test Solution')
        self.assertEqual(data['category'], 'Hydraulics')
        self.assertIn('id', data)

    def test_optional_english_fields_nullable(self):
        """Test English fields are optional/nullable."""
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_sv='Svenskt Problem',
            solution_sv='Svensk Lösning',
            category='Test',
            created_by=self.user
        )
        
        serializer = KnowledgeBaseEntrySerializer(instance=entry)
        data = serializer.data
        
        self.assertIsNone(data['issue_title_en'])
        self.assertIsNone(data['solution_en'])

    def test_optional_swedish_fields_nullable(self):
        """Test Swedish fields are optional/nullable."""
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_en='English Issue',
            solution_en='English Solution',
            category='Test',
            created_by=self.user
        )
        
        serializer = KnowledgeBaseEntrySerializer(instance=entry)
        data = serializer.data
        
        self.assertIsNone(data['issue_title_sv'])
        self.assertIsNone(data['solution_sv'])

    def test_category_required_field(self):
        """Test category is required."""
        data = {
            'issue_title_en': 'Test',
            'solution_en': 'Test'
        }
        serializer = KnowledgeBaseEntryCreateSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('category', serializer.errors)

    def test_status_choices_validation(self):
        """Test status choices validation."""
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_en='Test',
            solution_en='Test',
            category='Test',
            created_by=self.user
        )
        
        # Valid status
        data = {'status': 'active'}
        serializer = KnowledgeBaseEntrySerializer(instance=entry, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        # Invalid status
        data = {'status': 'invalid'}
        serializer = KnowledgeBaseEntrySerializer(instance=entry, data=data, partial=True)
        self.assertFalse(serializer.is_valid())

    def test_embedding_status_read_only(self):
        """Test embedding_status field is read-only."""
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_en='Test',
            solution_en='Test',
            category='Test',
            created_by=self.user
        )
        
        # Try to set embedding_status directly
        data = {
            'issue_title_en': 'Updated',
            'solution_en': 'Updated',
            'category': 'Test',
            'embedding_status': 'completed'  # Try to set this
        }
        serializer = KnowledgeBaseEntrySerializer(instance=entry, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_entry = serializer.save()
        
        # Embedding status should not change from user input
        self.assertEqual(updated_entry.embedding_status, entry.embedding_status)


class KnowledgeBaseEntryCreateSerializerTest(TestCase):
    """Test cases for KnowledgeBaseEntryCreateSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='pass123'
        )

    def test_create_entry_with_english_only(self):
        """Test creating entry with English content only."""
        data = {
            'issue_title_en': 'English Issue',
            'solution_en': 'English Solution',
            'category': 'Hydraulics'
        }
        serializer = KnowledgeBaseEntryCreateSerializer(
            data=data,
            context={'request': type('obj', (object,), {'user': self.user})}
        )
        
        self.assertTrue(serializer.is_valid())

    def test_create_entry_with_swedish_only(self):
        """Test creating entry with Swedish content only."""
        data = {
            'issue_title_sv': 'Svenskt Problem',
            'solution_sv': 'Svensk Lösning',
            'category': 'Hydraulik'
        }
        serializer = KnowledgeBaseEntryCreateSerializer(
            data=data,
            context={'request': type('obj', (object,), {'user': self.user})}
        )
        
        self.assertTrue(serializer.is_valid())

    def test_create_entry_with_both_languages(self):
        """Test creating entry with both languages."""
        data = {
            'issue_title_en': 'English Issue',
            'solution_en': 'English Solution',
            'issue_title_sv': 'Svenskt Problem',
            'solution_sv': 'Svensk Lösning',
            'category': 'Engine'
        }
        serializer = KnowledgeBaseEntryCreateSerializer(
            data=data,
            context={'request': type('obj', (object,), {'user': self.user})}
        )
        
        self.assertTrue(serializer.is_valid())

