"""
Shared test utilities and helpers.

Provides common test functionality:
- User factories
- Authentication helpers
- Base test cases
- Mock objects for external services
"""
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.models import User


# User Factory Functions

def create_test_user(username='testuser', password='testpass123', **kwargs):
    """
    Create a regular test user.
    
    Args:
        username: Username for the user
        password: Password for the user
        **kwargs: Additional user fields
    
    Returns:
        User instance
    """
    defaults = {
        'role': User.Role.USER
    }
    defaults.update(kwargs)
    
    return User.objects.create_user(
        username=username,
        password=password,
        **defaults
    )


def create_admin_user(username='admin', password='adminpass123', **kwargs):
    """
    Create an admin test user.
    
    Args:
        username: Username for the admin
        password: Password for the admin
        **kwargs: Additional user fields
    
    Returns:
        Admin User instance
    """
    defaults = {
        'role': User.Role.ADMIN
    }
    defaults.update(kwargs)
    
    return User.objects.create_user(
        username=username,
        password=password,
        **defaults
    )


def create_superuser(username='superuser', password='superpass123', **kwargs):
    """
    Create a superuser for testing.
    
    Args:
        username: Username for the superuser
        password: Password for the superuser
        **kwargs: Additional user fields
    
    Returns:
        Superuser instance
    """
    return User.objects.create_superuser(
        username=username,
        password=password,
        **kwargs
    )


# Authentication Helpers

def get_auth_token(user):
    """
    Get JWT authentication token for a user.
    
    Args:
        user: User instance
    
    Returns:
        dict with 'access' and 'refresh' tokens
    """
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh)
    }


def get_auth_header(user):
    """
    Get authentication header for API requests.
    
    Args:
        user: User instance
    
    Returns:
        dict with Authorization header
    """
    tokens = get_auth_token(user)
    return {
        'HTTP_AUTHORIZATION': f'Bearer {tokens["access"]}'
    }


# Base Test Case Classes

class APITestCaseBase(APITestCase):
    """
    Base test case class with common setup for API tests.
    
    Provides:
    - Admin and regular user setup
    - Authentication helpers
    - Common assertions
    """
    
    def setUp(self):
        """Set up common test data."""
        super().setUp()
        self.admin_user = create_admin_user()
        self.regular_user = create_test_user()
    
    def authenticate_as_admin(self):
        """Authenticate client as admin user."""
        self.client.force_authenticate(user=self.admin_user)
    
    def authenticate_as_user(self):
        """Authenticate client as regular user."""
        self.client.force_authenticate(user=self.regular_user)
    
    def assert_forbidden(self, response):
        """Assert response is 403 Forbidden."""
        self.assertEqual(response.status_code, 403)
    
    def assert_unauthorized(self, response):
        """Assert response is 401 Unauthorized."""
        self.assertEqual(response.status_code, 401)
    
    def assert_success(self, response):
        """Assert response is 2xx success."""
        self.assertTrue(200 <= response.status_code < 300)
    
    def assert_created(self, response):
        """Assert response is 201 Created."""
        self.assertEqual(response.status_code, 201)
    
    def assert_not_found(self, response):
        """Assert response is 404 Not Found."""
        self.assertEqual(response.status_code, 404)


# Mock Classes for External Services

class MockOpenAIEmbeddings:
    """Mock OpenAI embeddings for testing."""
    
    def __init__(self, *args, **kwargs):
        """Initialize mock."""
        pass
    
    def embed_query(self, text):
        """
        Mock embed_query method.
        
        Returns a fake embedding vector.
        """
        # Return a fake 1536-dimensional vector
        return [0.1] * 1536
    
    def embed_documents(self, texts):
        """
        Mock embed_documents method.
        
        Returns fake embedding vectors for multiple texts.
        """
        return [[0.1] * 1536 for _ in texts]


class MockPineconeIndex:
    """Mock Pinecone index for testing."""
    
    def __init__(self):
        """Initialize mock index."""
        self.vectors = {}
    
    def upsert(self, vectors):
        """Mock upsert method."""
        for vector_id, embedding, metadata in vectors:
            self.vectors[vector_id] = {
                'embedding': embedding,
                'metadata': metadata
            }
        return {'upserted_count': len(vectors)}
    
    def query(self, vector, top_k=5, filter=None, include_metadata=False):
        """Mock query method."""
        # Return mock search results
        matches = []
        for vec_id, vec_data in list(self.vectors.items())[:top_k]:
            match = {
                'id': vec_id,
                'score': 0.95,
                'metadata': vec_data['metadata'] if include_metadata else {}
            }
            matches.append(match)
        
        return {'matches': matches}
    
    def delete(self, ids):
        """Mock delete method."""
        for vec_id in ids:
            self.vectors.pop(vec_id, None)
        return {'deleted_count': len(ids)}


class MockPineconeClient:
    """Mock Pinecone client for testing."""
    
    def __init__(self, *args, **kwargs):
        """Initialize mock client."""
        self._index = MockPineconeIndex()
    
    def Index(self, name):
        """Return mock index."""
        return self._index


# Test Data Factories

class TestDataFactory:
    """Factory class for creating test data."""
    
    @staticmethod
    def create_conversation(user, **kwargs):
        """Create a test conversation."""
        from apps.conversations.models import ConversationHistory
        
        defaults = {
            'session_id': 'test_session',
            'user_query': 'Test query',
            'ai_response': 'Test response',
            'language': 'en',
            'response_time': 1000,
            'status': 'active'
        }
        defaults.update(kwargs)
        
        return ConversationHistory.objects.create(
            user=user,
            **defaults
        )
    
    @staticmethod
    def create_escalation(**kwargs):
        """Create a test escalation."""
        from apps.escalations.models import Escalation
        
        defaults = {
            'customer_name': 'Test Customer',
            'customer_email': 'test@example.com',
            'equipment_id': 'TEST-001',
            'problem_description': 'Test problem',
            'language': 'en'
        }
        defaults.update(kwargs)
        
        return Escalation.objects.create(**defaults)
    
    @staticmethod
    def create_knowledge_base_entry(user, **kwargs):
        """Create a test knowledge base entry."""
        from apps.knowledge_base.models import KnowledgeBaseEntry
        
        defaults = {
            'issue_title_en': 'Test Issue',
            'solution_en': 'Test Solution',
            'category': 'Test'
        }
        defaults.update(kwargs)
        
        return KnowledgeBaseEntry.objects.create(
            created_by=user,
            **defaults
        )

