"""
Authentication Service for Arcadia Platform
Implements secure authentication with JWT tokens, password hashing, and audit logging
"""
import bcrypt
import jwt
import re
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config'))

# Try importing settings with fallback
try:
    from settings import settings
except ImportError:
    # Fallback settings class
    class FallbackSettings:
        JWT_SECRET_KEY = "change-me-in-production"
        JWT_ALGORITHM = "HS256"
        JWT_EXPIRATION_HOURS = 24
        DEFAULT_TOKENS = 100
    settings = FallbackSettings()

# Import models
from models.database import User, AuditLog, db_manager

class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass

class AuthorizationError(Exception):
    """Custom exception for authorization errors"""
    pass

class AuthService:
    """
    Secure authentication service implementing the requirements from the project document.
    Features:
    - Secure password hashing with bcrypt
    - JWT token generation and validation
    - Email validation
    - Rate limiting protection
    - Comprehensive audit logging
    """
    
    def __init__(self):
        self.failed_attempts = {}  # Simple in-memory rate limiting
        self.max_attempts = 5
        self.lockout_duration = 300  # 5 minutes
    
    def _hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt with salt
        Addresses MS.02 (password security) from the document
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def _validate_email(self, email: str) -> bool:
        """
        Validate email format using regex
        Input validation as per security requirements
        """
        if not email or len(email) > 255:
            return False
        
        # Basic email regex that prevents consecutive dots
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False
        
        # Check for consecutive dots (not allowed)
        if '..' in email:
            return False
        
        # Check for starting or ending with dot
        local_part = email.split('@')[0]
        if local_part.startswith('.') or local_part.endswith('.'):
            return False
        
        return True
    
    def _validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """
        Validate password strength
        Requirements: min 8 chars, uppercase, lowercase, number, special char
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, "Password meets requirements"
    
    def _validate_username(self, username: str) -> Tuple[bool, str]:
        """Validate username format and length"""
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if len(username) > 50:
            return False, "Username cannot exceed 50 characters"
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"
        
        return True, "Username is valid"
    
    def _check_rate_limit(self, identifier: str) -> bool:
        """
        Check if identifier (email/IP) is rate limited
        Protects against brute force attacks (MS.02)
        """
        current_time = time.time()
        
        if identifier in self.failed_attempts:
            attempts, last_attempt = self.failed_attempts[identifier]
            
            # Reset if lockout period has passed
            if current_time - last_attempt > self.lockout_duration:
                del self.failed_attempts[identifier]
                return True
            
            # Check if still locked out
            if attempts >= self.max_attempts:
                return False
        
        return True
    
    def _record_failed_attempt(self, identifier: str):
        """Record a failed authentication attempt"""
        current_time = time.time()
        
        if identifier in self.failed_attempts:
            attempts, _ = self.failed_attempts[identifier]
            self.failed_attempts[identifier] = (attempts + 1, current_time)
        else:
            self.failed_attempts[identifier] = (1, current_time)
    
    def _clear_failed_attempts(self, identifier: str):
        """Clear failed attempts after successful authentication"""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]
    
    def _log_audit_event(self, session: Session, action: str, user_id: Optional[uuid.UUID] = None, 
                        details: Dict = None, severity: str = "INFO"):
        """
        Log security and authentication events
        Implements comprehensive audit logging as per PBI-07
        """
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type="authentication",
                details=details or {},
                severity=severity
            )
            session.add(audit_log)
            session.flush()  # Don't commit yet, let the calling function handle it
        except Exception as e:
            print(f"Warning: Failed to log audit event: {e}")
    
    def generate_token(self, user_id: uuid.UUID, username: str) -> str:
        """
        Generate JWT token for authenticated user
        Implements secure token generation with expiration
        """
        payload = {
            "user_id": str(user_id),
            "username": username,
            "iat": int(time.time()),
            "exp": int(time.time()) + (settings.JWT_EXPIRATION_HOURS * 3600),
            "jti": str(uuid.uuid4())  # JWT ID for token tracking
        }
        
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> Dict:
        """
        Verify and decode JWT token
        Returns user information if valid, raises exception if invalid
        """
        try:
            decoded = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            return decoded
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
    
    def register_user(self, email: str, username: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """
        Register a new user with validation and security checks
        Implements secure user registration as per PBI-01A
        """
        session = db_manager.get_session()
        
        try:
            # Input validation
            if not self._validate_email(email):
                return False, "Invalid email format", None
            
            username_valid, username_msg = self._validate_username(username)
            if not username_valid:
                return False, username_msg, None
            
            password_valid, password_msg = self._validate_password_strength(password)
            if not password_valid:
                return False, password_msg, None
            
            # Check rate limiting
            if not self._check_rate_limit(email):
                self._log_audit_event(session, "REGISTRATION_RATE_LIMITED", 
                                    details={"email": email}, severity="WARNING")
                return False, "Too many registration attempts. Please try again later.", None
            
            # Hash password
            password_hash = self._hash_password(password)
            
            # Create user
            user = User(
                email=email,
                username=username,
                password_hash=password_hash,
                tokens=settings.DEFAULT_TOKENS,
                profile_data={"created_via": "terminal"}
            )
            
            session.add(user)
            session.flush()  # Get the user ID
            
            # Log successful registration
            self._log_audit_event(session, "USER_REGISTERED", user.id, 
                                {"email": email, "username": username})
            
            session.commit()
            self._clear_failed_attempts(email)
            
            # Refresh the user object to ensure all attributes are loaded
            # and detach it from the session so it can be used after session.close()
            session.refresh(user)
            session.expunge(user)  # Detach from session
            
            return True, "User registered successfully", user
            
        except IntegrityError as e:
            session.rollback()
            if "email" in str(e):
                error_msg = "Email already exists"
            elif "username" in str(e):
                error_msg = "Username already exists"
            else:
                error_msg = "Registration failed: user already exists"
            
            self._log_audit_event(session, "REGISTRATION_FAILED", 
                                details={"email": email, "error": error_msg}, severity="WARNING")
            self._record_failed_attempt(email)
            
            return False, error_msg, None
            
        except Exception as e:
            session.rollback()
            self._log_audit_event(session, "REGISTRATION_ERROR", 
                                details={"email": email, "error": str(e)}, severity="ERROR")
            return False, f"Registration failed: {str(e)}", None
            
        finally:
            session.close()
    
    def authenticate_user(self, email: str, password: str) -> Tuple[bool, str, Optional[str], Optional[User]]:
        """
        Authenticate user and return JWT token
        Implements secure authentication as per US.M.01 and addresses MS.02
        """
        session = db_manager.get_session()
        
        try:
            # Input validation
            if not self._validate_email(email):
                return False, "Invalid email format", None, None
            
            # Check rate limiting
            if not self._check_rate_limit(email):
                self._log_audit_event(session, "LOGIN_RATE_LIMITED", 
                                    details={"email": email}, severity="WARNING")
                return False, "Too many login attempts. Please try again later.", None, None
            
            # Find user
            user = session.query(User).filter(User.email == email, User.is_active == True).first()
            
            if not user:
                self._record_failed_attempt(email)
                self._log_audit_event(session, "LOGIN_FAILED_USER_NOT_FOUND", 
                                    details={"email": email}, severity="WARNING")
                return False, "Invalid email or password", None, None
            
            # Verify password
            if not self._verify_password(password, user.password_hash):
                self._record_failed_attempt(email)
                self._log_audit_event(session, "LOGIN_FAILED_WRONG_PASSWORD", user.id,
                                    details={"email": email}, severity="WARNING")
                return False, "Invalid email or password", None, None
            
            # Generate token
            token = self.generate_token(user.id, user.username)
            
            # Update last login
            user.last_login = datetime.now(timezone.utc)
            
            # Log successful login
            self._log_audit_event(session, "LOGIN_SUCCESS", user.id, 
                                {"email": email, "username": user.username})
            
            session.commit()
            self._clear_failed_attempts(email)
            
            # Refresh the user object to ensure all attributes are loaded
            # and detach it from the session so it can be used after session.close()
            session.refresh(user)
            session.expunge(user)  # Detach from session
            
            return True, "Login successful", token, user
            
        except Exception as e:
            session.rollback()
            self._log_audit_event(session, "LOGIN_ERROR", 
                                details={"email": email, "error": str(e)}, severity="ERROR")
            return False, f"Authentication failed: {str(e)}", None, None
            
        finally:
            session.close()
    
    def validate_session(self, token: str) -> Tuple[bool, Optional[User]]:
        """
        Validate user session token and return user if valid
        """
        session = db_manager.get_session()
        
        try:
            # Verify token
            decoded = self.verify_token(token)
            user_id = uuid.UUID(decoded["user_id"])
            
            # Get user from database
            user = session.query(User).filter(
                User.id == user_id, 
                User.is_active == True
            ).first()
            
            if not user:
                raise AuthenticationError("User not found or inactive")
            
            # Refresh the user object to ensure all attributes are loaded
            # and detach it from the session so it can be used after session.close()
            session.refresh(user)
            session.expunge(user)  # Detach from session
            
            return True, user
            
        except AuthenticationError:
            return False, None
        except Exception as e:
            print(f"Session validation error: {e}")
            return False, None
        finally:
            session.close()
    
    def logout_user(self, token: str) -> bool:
        """
        Logout user and invalidate token
        Note: In a production system, you would maintain a token blacklist
        """
        session = db_manager.get_session()
        
        try:
            decoded = self.verify_token(token)
            user_id = uuid.UUID(decoded["user_id"])
            
            self._log_audit_event(session, "LOGOUT", user_id, 
                                {"username": decoded.get("username", "unknown")})
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            print(f"Logout error: {e}")
            return False
        finally:
            session.close()
    
    def change_password(self, user_id: uuid.UUID, old_password: str, new_password: str) -> Tuple[bool, str]:
        """
        Change user password with validation
        """
        session = db_manager.get_session()
        
        try:
            # Validate new password
            password_valid, password_msg = self._validate_password_strength(new_password)
            if not password_valid:
                return False, password_msg
            
            # Get user
            user = session.query(User).filter(User.id == user_id, User.is_active == True).first()
            if not user:
                return False, "User not found"
            
            # Verify old password
            if not self._verify_password(old_password, user.password_hash):
                self._log_audit_event(session, "PASSWORD_CHANGE_FAILED", user.id, 
                                    details={"reason": "wrong_old_password"}, severity="WARNING")
                return False, "Current password is incorrect"
            
            # Update password
            user.password_hash = self._hash_password(new_password)
            
            self._log_audit_event(session, "PASSWORD_CHANGED", user.id)
            
            session.commit()
            return True, "Password changed successfully"
            
        except Exception as e:
            session.rollback()
            self._log_audit_event(session, "PASSWORD_CHANGE_ERROR", user_id,
                                details={"error": str(e)}, severity="ERROR")
            return False, f"Password change failed: {str(e)}"
        finally:
            session.close()

# Global auth service instance
auth_service = AuthService()