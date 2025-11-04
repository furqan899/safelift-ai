"""
Tests for KnowledgeBase models.
"""
from django.test import TestCase
from apps.knowledge_base.models import KnowledgeBaseEntry
from apps.users.models import User


class KnowledgeBaseEntryModelTest(TestCase):
    """Test cases for KnowledgeBaseEntry model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='pass123'
        )

    def test_knowledge_base_entry_creation_with_uuid(self):
        """Test creating entry with UUID primary key."""
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_en='Test Issue',
            solution_en='Test Solution',
            category='Hydraulics',
            created_by=self.user
        )
        
        self.assertIsNotNone(entry.id)
        # UUID should be string type
        self.assertIsInstance(str(entry.id), str)

    def test_bilingual_content_english_only(self):
        """Test entry with English content only."""
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_en='English Issue',
            solution_en='English Solution',
            category='Brakes',
            created_by=self.user
        )
        
        self.assertEqual(entry.issue_title_en, 'English Issue')
        self.assertEqual(entry.solution_en, 'English Solution')
        self.assertIsNone(entry.issue_title_sv)
        self.assertIsNone(entry.solution_sv)

    def test_bilingual_content_swedish_only(self):
        """Test entry with Swedish content only."""
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_sv='Svenskt Problem',
            solution_sv='Svensk Lösning',
            category='Motor',
            created_by=self.user
        )
        
        self.assertEqual(entry.issue_title_sv, 'Svenskt Problem')
        self.assertEqual(entry.solution_sv, 'Svensk Lösning')
        self.assertIsNone(entry.issue_title_en)
        self.assertIsNone(entry.solution_en)

    def test_bilingual_content_both_languages(self):
        """Test entry with both English and Swedish content."""
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_en='English Issue',
            solution_en='English Solution',
            issue_title_sv='Svenskt Problem',
            solution_sv='Svensk Lösning',
            category='Engine',
            created_by=self.user
        )
        
        self.assertIsNotNone(entry.issue_title_en)
        self.assertIsNotNone(entry.solution_en)
        self.assertIsNotNone(entry.issue_title_sv)
        self.assertIsNotNone(entry.solution_sv)

    def test_get_combined_content_en_returns_correct_format(self):
        """Test get_combined_content_en method."""
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_en='Test Issue',
            solution_en='Test Solution',
            category='Hydraulics',
            created_by=self.user
        )
        
        combined = entry.get_combined_content_en()
        
        self.assertIn('Test Issue', combined)
        self.assertIn('Test Solution', combined)
        self.assertIn('\n\n', combined)

    def test_get_combined_content_sv_returns_correct_format(self):
        """Test get_combined_content_sv method."""
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_sv='Test Problem',
            solution_sv='Test Lösning',
            category='Hydraulik',
            created_by=self.user
        )
        
        combined = entry.get_combined_content_sv()
        
        self.assertIn('Test Problem', combined)
        self.assertIn('Test Lösning', combined)
        self.assertIn('\n\n', combined)

    def test_has_both_languages_returns_true(self):
        """Test has_both_languages returns True when both languages present."""
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_en='English Issue',
            solution_en='English Solution',
            issue_title_sv='Svenskt Problem',
            solution_sv='Svensk Lösning',
            category='Engine',
            created_by=self.user
        )
        
        self.assertTrue(entry.has_both_languages())

    def test_has_both_languages_returns_false_english_only(self):
        """Test has_both_languages returns False with English only."""
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_en='English Issue',
            solution_en='English Solution',
            category='Engine',
            created_by=self.user
        )
        
        self.assertFalse(entry.has_both_languages())

    def test_has_both_languages_returns_false_swedish_only(self):
        """Test has_both_languages returns False with Swedish only."""
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_sv='Svenskt Problem',
            solution_sv='Svensk Lösning',
            category='Motor',
            created_by=self.user
        )
        
        self.assertFalse(entry.has_both_languages())

    def test_is_active_checks_status(self):
        """Test is_active method checks status field."""
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_en='Test',
            solution_en='Test',
            category='Test',
            created_by=self.user,
            status=KnowledgeBaseEntry.Status.ACTIVE
        )
        
        self.assertTrue(entry.is_active())
        
        entry.status = KnowledgeBaseEntry.Status.INACTIVE
        entry.save()
        
        self.assertFalse(entry.is_active())

    def test_is_embedding_complete_checks_embedding_status(self):
        """Test is_embedding_complete method."""
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_en='Test',
            solution_en='Test',
            category='Test',
            created_by=self.user,
            embedding_status=KnowledgeBaseEntry.EmbeddingStatus.COMPLETED
        )
        
        self.assertTrue(entry.is_embedding_complete())
        
        entry.embedding_status = KnowledgeBaseEntry.EmbeddingStatus.PENDING
        entry.save()
        
        self.assertFalse(entry.is_embedding_complete())

    def test_status_choices(self):
        """Test status choices are correctly defined."""
        choices = KnowledgeBaseEntry.Status.choices
        
        self.assertEqual(len(choices), 2)
        self.assertIn(('active', 'Active'), choices)
        self.assertIn(('inactive', 'Inactive'), choices)

    def test_embedding_status_choices(self):
        """Test embedding status choices are correctly defined."""
        choices = KnowledgeBaseEntry.EmbeddingStatus.choices
        
        self.assertEqual(len(choices), 4)
        self.assertIn(('pending', 'Pending'), choices)
        self.assertIn(('processing', 'Processing'), choices)
        self.assertIn(('completed', 'Completed'), choices)
        self.assertIn(('failed', 'Failed'), choices)

    def test_string_representation(self):
        """Test __str__ method."""
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_en='English Title',
            solution_en='Solution',
            category='Hydraulics',
            created_by=self.user
        )
        
        expected = 'English Title (Hydraulics)'
        self.assertEqual(str(entry), expected)

    def test_string_representation_with_swedish_only(self):
        """Test __str__ method with Swedish content only."""
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_sv='Svensk Titel',
            solution_sv='Lösning',
            category='Hydraulik',
            created_by=self.user
        )
        
        expected = 'Svensk Titel (Hydraulik)'
        self.assertEqual(str(entry), expected)

    def test_default_values(self):
        """Test default values are set correctly."""
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_en='Test',
            solution_en='Test',
            category='Test',
            created_by=self.user
        )
        
        self.assertEqual(entry.status, KnowledgeBaseEntry.Status.ACTIVE)
        self.assertEqual(entry.embedding_status, KnowledgeBaseEntry.EmbeddingStatus.PENDING)
        self.assertEqual(entry.pinecone_vector_ids, [])
        self.assertEqual(entry.metadata, {})
        self.assertEqual(entry.tags, [])

    def test_ordering(self):
        """Test default ordering by created_at descending."""
        entry1 = KnowledgeBaseEntry.objects.create(
            issue_title_en='First',
            solution_en='First',
            category='Test',
            created_by=self.user
        )
        entry2 = KnowledgeBaseEntry.objects.create(
            issue_title_en='Second',
            solution_en='Second',
            category='Test',
            created_by=self.user
        )
        
        entries = list(KnowledgeBaseEntry.objects.all())
        
        # Most recent should be first
        self.assertEqual(entries[0].id, entry2.id)
        self.assertEqual(entries[1].id, entry1.id)

