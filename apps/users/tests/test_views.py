"""
Tests for User views.
"""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.models import User


class UserListCreateViewTest(APITestCase):
    """Test cases for UserListCreateView."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            role=User.Role.ADMIN
        )
        self.regular_user = User.objects.create_user(
            username='user',
            password='userpass123',
            role=User.Role.USER
        )
        self.list_url = reverse('users:user-list-create')

    def test_list_users_as_admin(self):
        """Test admin can list all users."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Response is a simple list (no pagination configured)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 2)

    def test_list_users_as_regular_user_denied(self):
        """Test regular user cannot list all users."""
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_users_without_authentication(self):
        """Test listing users requires authentication."""
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_user_as_admin(self):
        """Test admin can create new user."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'username': 'newuser',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'role': 'USER'
        }
        response = self.client.post(self.list_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'newuser')
        self.assertEqual(response.data['role'], 'USER')
        
        # Verify user was created in database
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_create_user_as_regular_user_denied(self):
        """Test regular user cannot create users."""
        self.client.force_authenticate(user=self.regular_user)
        
        data = {
            'username': 'newuser',
            'password': 'pass123',
            'role': 'USER'
        }
        response = self.client.post(self.list_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_pagination_works(self):
        """Test pagination works correctly."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create multiple users
        for i in range(25):
            User.objects.create_user(
                username=f'user{i}',
                password='pass123'
            )
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 20)


class UserDetailViewTest(APITestCase):
    """Test cases for UserDetailView."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            role=User.Role.ADMIN
        )
        self.user1 = User.objects.create_user(
            username='user1',
            password='pass123',
            role=User.Role.USER
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='pass123',
            role=User.Role.USER
        )

    def get_detail_url(self, user_id):
        """Helper to get detail URL for a user."""
        return reverse('users:user-detail', kwargs={'pk': user_id})

    def test_retrieve_own_data(self):
        """Test user can retrieve their own data."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_detail_url(self.user1.id)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'user1')

    def test_retrieve_other_user_as_admin(self):
        """Test admin can retrieve any user's data."""
        self.client.force_authenticate(user=self.admin_user)
        url = self.get_detail_url(self.user1.id)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'user1')

    def test_retrieve_other_user_as_regular_user_denied(self):
        """Test regular user cannot retrieve other user's data."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_detail_url(self.user2.id)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_own_data(self):
        """Test user can update their own data."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_detail_url(self.user1.id)
        
        data = {
            'username': 'user1',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'role': 'USER'
        }
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password was changed
        self.user1.refresh_from_db()
        self.assertTrue(self.user1.check_password('newpass123'))

    def test_partial_update_own_data(self):
        """Test user can partially update their own data."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_detail_url(self.user1.id)
        
        data = {'password': 'updatedpass'}
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify only password was changed
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.username, 'user1')
        self.assertTrue(self.user1.check_password('updatedpass'))

    def test_update_other_user_as_admin(self):
        """Test admin can update any user."""
        self.client.force_authenticate(user=self.admin_user)
        url = self.get_detail_url(self.user1.id)
        
        data = {
            'username': 'user1',
            'password': 'pass12345',
            'password_confirm': 'pass12345',
            'role': 'ADMIN'
        }
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'ADMIN')

    def test_update_other_user_as_regular_user_denied(self):
        """Test regular user cannot update other users."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_detail_url(self.user2.id)
        
        data = {
            'username': 'user2',
            'password': 'pass123',
            'role': 'USER'
        }
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_user_as_admin(self):
        """Test admin can delete users."""
        self.client.force_authenticate(user=self.admin_user)
        url = self.get_detail_url(self.user1.id)
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.user1.id).exists())

    def test_delete_user_as_regular_user_denied(self):
        """Test regular user cannot delete users."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_detail_url(self.user2.id)
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(User.objects.filter(id=self.user2.id).exists())

    def test_delete_own_account_denied(self):
        """Test user cannot delete their own account."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_detail_url(self.user1.id)
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_nonexistent_user(self):
        """Test retrieving non-existent user returns 404."""
        self.client.force_authenticate(user=self.admin_user)
        url = self.get_detail_url(99999)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

