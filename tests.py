import json
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
import uuid
from api.models import User, Customer
from api.interfaces.jwttokens import TokenExpiredError, InvalidTokenError, BlacklistedTokenError


class CustomerManagerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            name='Test User',
            email='test@example.com',
            openid_user_id=str(uuid.uuid4()),
        )
        self.user.phone_number = '+1234567890'
        self.user.save()

        self.client = Client()

        self.create_url = reverse('create_customer')

        self.token = "fake_jwt_token_for_testing"

        self.decode_token_patcher = patch('api.interfaces.jwttokens.decode_token')
        self.mock_decode_token = self.decode_token_patcher.start()
        self.mock_decode_token.return_value = {
            'user_id': str(self.user.id),
            'username': self.user.name,
            'email': self.user.email,
            'is_staff': False
        }
        self.addCleanup(self.decode_token_patcher.stop)

        self.get_token_patcher = patch('api.interfaces.jwttokens.get_token_from_request')
        self.mock_get_token = self.get_token_patcher.start()
        self.mock_get_token.return_value = self.token
        self.addCleanup(self.get_token_patcher.stop)

    def test_create_customer_success(self):
        """Test successful customer creation"""
        data = {
            "name": "Test Customer",
            "user_id": str(self.user.id)
        }

        response = self.client.post(
            self.create_url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['message'], 'Customer created successfully')
        self.assertTrue('customer_id' in response_data)
        self.assertTrue('customer_code' in response_data)

        customer = Customer.objects.get(name='Test Customer')
        self.assertEqual(customer.user, self.user)
        self.assertEqual(len(customer.code), 8)

    def test_create_customer_missing_name(self):
        """Test customer creation with missing name"""
        data = {
            "user_id": str(self.user.id)
        }

        response = self.client.post(
            self.create_url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'Name is required')

    def test_create_customer_missing_user_id(self):
        """Test customer creation with missing user_id"""
        data = {
            "name": "Test Customer"
        }

        response = self.client.post(
            self.create_url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'User ID is required')

    def test_create_customer_invalid_user_id(self):
        """Test customer creation with invalid user_id"""
        non_existent_uuid = str(uuid.uuid4())

        data = {
            "name": "Test Customer",
            "user_id": non_existent_uuid
        }

        response = self.client.post(
            self.create_url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.content)
        self.assertIn('User matching query does not exist', str(response_data['error']))

    def test_create_customer_user_without_phone(self):
        """Test customer creation with a user that has no phone number"""
        user_no_phone = User.objects.create(
            name='No Phone User',
            email='nophone@example.com',
            openid_user_id=str(uuid.uuid4()),
        )

        data = {
            "name": "Test Customer",
            "user_id": str(user_no_phone.id)
        }

        response = self.client.post(
            self.create_url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'User phone number is required kindly add phone number to the user ')

    def test_create_customer_wrong_method(self):
        """Test customer creation with wrong HTTP method"""
        response = self.client.get(self.create_url)

        self.assertEqual(response.status_code, 405)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'Invalid request method, kindly use POST Request')

    def test_unique_customer_code(self):
        """Test that each customer gets a unique code"""
        codes = set()
        for i in range(5):
            data = {
                "name": f"Customer {i}",
                "user_id": str(self.user.id)
            }

            response = self.client.post(
                self.create_url,
                data=json.dumps(data),
                content_type='application/json'
            )

            self.assertEqual(response.status_code, 201)
            response_data = json.loads(response.content)
            codes.add(response_data['customer_code'])
        self.assertEqual(len(codes), 5)

    def test_authentication_required(self):
        """Test that authentication is required"""
        self.mock_get_token.return_value = None

        data = {
            "name": "Test Customer",
            "user_id": str(self.user.id)
        }

        response = self.client.post(
            self.create_url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'Authentication required')
        self.mock_get_token.return_value = self.token

    def test_token_expired(self):
        """Test behavior when token has expired"""
        self.mock_decode_token.side_effect = TokenExpiredError("Token has expired")

        data = {
            "name": "Test Customer",
            "user_id": str(self.user.id)
        }

        response = self.client.post(
            self.create_url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'Token has expired')
        self.assertEqual(response_data['code'], 'token_expired')
        self.mock_decode_token.side_effect = None
        self.mock_decode_token.return_value = {
            'user_id': str(self.user.id),
            'username': self.user.name,
            'email': self.user.email,
            'is_staff': False
        }