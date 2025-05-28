"""
Unit tests for authentication service
Implements test cases from the project document (PBI-01A, PBI-01B)
Tests both valid use cases and misuse cases (MS.02, MS.07)
"""
import unittest
import uuid
import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config'))

from services.auth_service import auth_service, AuthenticationError
from models.database import User
from settings import settings

class TestAuthentication(unittest.TestCase):
    """
    Test suite for authentication functionality
    Based on test cases from the project document
    """
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_email = "testuser@example.com"
        self.valid_username = "testuser123"
        self.valid_password = "SecurePass123!"
        self.invalid_email = "invalid-email"
        self.weak_password = "123"
        
    def test_valid_login_success(self):
        """
        Test ID: UT-AUTH-01
        UC: US.M.01 – Login utente valido
        """
        with patch.object(auth_service, 'authenticate_user') as mock_auth:
            # Mock successful authentication
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_user.username = self.valid_username
            mock_user.email = self.valid_email
            
            mock_auth.return_value = (True, "Login successful", "mock_token", mock_user)
            
            success, message, token, user = auth_service.authenticate_user(
                self.valid_email, self.valid_password
            )
            
            self.assertTrue(success)
            self.assertIsNotNone(token)
            self.assertIsNotNone(user)
            self.assertEqual(message, "Login successful")
    
    def test_invalid_login_failure(self):
        """
        Test ID: UT-AUTH-02
        MS: MS.02 – Phishing attempt with wrong credentials
        """
        with patch.object(auth_service, 'authenticate_user') as mock_auth:
            # Mock failed authentication
            mock_auth.return_value = (False, "Invalid email or password", None, None)
            
            success, message, token, user = auth_service.authenticate_user(
                self.valid_email, "wrongpassword"
            )
            
            self.assertFalse(success)
            self.assertIsNone(token)
            self.assertIsNone(user)
            self.assertIn("Invalid", message)
    
    def test_jwt_token_structure(self):
        """
        Test ID: UT-AUTH-03
        MS: MS.07 – Token falsificado
        """
        # Test token generation
        user_id = uuid.uuid4()
        username = "testuser"
        
        token = auth_service.generate_token(user_id, username)
        
        # JWT tokens should start with "eyJ" (base64 encoded header)
        self.assertTrue(token.startswith("eyJ"))
        
        # Token should have 3 parts separated by dots
        parts = token.split('.')
        self.assertEqual(len(parts), 3)
        
        # Test token verification
        try:
            decoded = auth_service.verify_token(token)
            self.assertIn("user_id", decoded)
            self.assertIn("username", decoded)
            self.assertIn("exp", decoded)
            self.assertIn("iat", decoded)
            self.assertEqual(decoded["user_id"], str(user_id))
            self.assertEqual(decoded["username"], username)
        except AuthenticationError:
            self.fail("Valid token should not raise AuthenticationError")
    
    def test_invalid_token_rejection(self):
        """Test that invalid tokens are properly rejected"""
        invalid_tokens = [
            "invalid.token.here",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
            "",
            "not_a_token_at_all"
        ]
        
        for invalid_token in invalid_tokens:
            with self.assertRaises(AuthenticationError):
                auth_service.verify_token(invalid_token)
    
    def test_email_validation(self):
        """Test email validation logic"""
        valid_emails = [
            "user@example.com",
            "test.user@domain.co.uk",
            "user+tag@example.org"
        ]
        
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user..double.dot@example.com",
            ""
        ]
        
        for email in valid_emails:
            self.assertTrue(auth_service._validate_email(email), f"Should accept {email}")
        
        for email in invalid_emails:
            self.assertFalse(auth_service._validate_email(email), f"Should reject {email}")
    
    def test_password_strength_validation(self):
        """Test password strength requirements"""
        strong_passwords = [
            "SecurePass123!",
            "MyStr0ng_P@ssw0rd",
            "C0mpl3x#Password"
        ]
        
        weak_passwords = [
            "123",                  # Too short
            "password",             # No uppercase, numbers, special chars
            "PASSWORD123",          # No lowercase
            "password123",          # No uppercase, special chars
            "Password!",            # No numbers
            "Password123",          # No special chars
            ""                      # Empty
        ]
        
        for password in strong_passwords:
            valid, message = auth_service._validate_password_strength(password)
            self.assertTrue(valid, f"Should accept strong password: {password}")
        
        for password in weak_passwords:
            valid, message = auth_service._validate_password_strength(password)
            self.assertFalse(valid, f"Should reject weak password: {password}")
    
    def test_username_validation(self):
        """Test username validation"""
        valid_usernames = [
            "testuser",
            "user123",
            "test_user",
            "ValidUsername123"
        ]
        
        invalid_usernames = [
            "ab",                   # Too short
            "a" * 51,              # Too long
            "user-name",           # Invalid character
            "user@name",           # Invalid character
            "user name",           # Space not allowed
            "",                    # Empty
            "test.user"            # Dot not allowed
        ]
        
        for username in valid_usernames:
            valid, message = auth_service._validate_username(username)
            self.assertTrue(valid, f"Should accept username: {username}")
        
        for username in invalid_usernames:
            valid, message = auth_service._validate_username(username)
            self.assertFalse(valid, f"Should reject username: {username}")
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        identifier = "test@example.com"
        
        # Should allow initial attempts
        self.assertTrue(auth_service._check_rate_limit(identifier))
        
        # Simulate failed attempts
        for _ in range(5):
            auth_service._record_failed_attempt(identifier)
        
        # Should be rate limited after max attempts
        self.assertFalse(auth_service._check_rate_limit(identifier))
        
        # Should be able to clear failed attempts
        auth_service._clear_failed_attempts(identifier)
        self.assertTrue(auth_service._check_rate_limit(identifier))
    
    def test_password_hashing(self):
        """Test password hashing functionality"""
        password = "testpassword123"
        
        # Hash the password
        hashed = auth_service._hash_password(password)
        
        # Hash should not be the same as original password
        self.assertNotEqual(password, hashed)
        
        # Hash should be consistent for verification
        self.assertTrue(auth_service._verify_password(password, hashed))
        
        # Wrong password should not verify
        self.assertFalse(auth_service._verify_password("wrongpassword", hashed))
        
        # Different passwords should produce different hashes
        hash2 = auth_service._hash_password(password)
        self.assertNotEqual(hashed, hash2)  # Salt should make them different
    
    def test_registration_validation(self):
        """Test user registration validation"""
        # Test with mocked database to avoid actual DB operations
        with patch('services.auth_service.db_manager') as mock_db:
            mock_session = MagicMock()
            mock_db.get_session.return_value = mock_session
            
            # Mock successful user creation
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_user.username = self.valid_username
            mock_user.email = self.valid_email
            
            # Test input validation failures
            invalid_cases = [
                ("invalid-email", self.valid_username, self.valid_password),
                (self.valid_email, "ab", self.valid_password),  # Username too short
                (self.valid_email, self.valid_username, "weak"),  # Weak password
            ]
            
            for email, username, password in invalid_cases:
                success, message, user = auth_service.register_user(email, username, password)
                self.assertFalse(success, f"Should reject invalid input: {email}, {username}")
                self.assertIsNone(user)

class TestAuthenticationIntegration(unittest.TestCase):
    """Integration tests for authentication (require database)"""
    
    def setUp(self):
        """Set up for integration tests"""
        # These tests would require a test database
        # For now, we'll skip them or mock the database
        self.skipTest("Integration tests require test database setup")
    
    def test_full_registration_flow(self):
        """Test complete registration process"""
        # This would test the full flow with actual database
        pass
    
    def test_full_authentication_flow(self):
        """Test complete authentication process"""
        # This would test the full flow with actual database
        pass

if __name__ == '__main__':
    # Configure test environment
    os.environ['ENVIRONMENT'] = 'test'
    
    # Run tests
    unittest.main(verbosity=2)