"""
Security Utilities for Arcadia Platform
Implements security validation, monitoring, and threat detection
Based on STRIDE threat modeling from the project document
"""
import os
import re
import sys
import hashlib
import secrets
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config'))

# Try importing settings with fallback
try:
    from settings import settings
except ImportError:
    # Fallback settings class
    class FallbackSettings:
        JWT_SECRET_KEY = "change-me-in-production"
        DATABASE_URL = "postgresql://arcadia_user:arcadia_pass@localhost:5432/arcadia"
        ENVIRONMENT = "development"
    settings = FallbackSettings()

class SecurityValidator:
    """
    Security configuration and runtime validation
    Implements security checks based on the STRIDE analysis from the project document
    """
    
    def __init__(self):
        self.security_issues = []
        self.security_recommendations = []
    
    def validate_configuration(self) -> List[str]:
        """
        Validate security configuration
        Returns list of security issues found
        """
        issues = []
        
        # Check JWT configuration
        jwt_issues = self._validate_jwt_config()
        issues.extend(jwt_issues)
        
        # Check database configuration
        db_issues = self._validate_database_config()
        issues.extend(db_issues)
        
        # Check environment configuration
        env_issues = self._validate_environment_config()
        issues.extend(env_issues)
        
        # Check file permissions
        file_issues = self._validate_file_permissions()
        issues.extend(file_issues)
        
        return issues
    
    def _validate_jwt_config(self) -> List[str]:
        """Validate JWT security configuration"""
        issues = []
        
        # Check JWT secret strength
        if hasattr(settings, 'JWT_SECRET_KEY'):
            secret = settings.JWT_SECRET_KEY
            
            if len(secret) < 32:
                issues.append("JWT secret key is too short (should be at least 32 characters)")
            
            if secret in ['change-me-in-production', 'your-super-secret-jwt-key-change-in-production']:
                issues.append("JWT secret key is using default value - CRITICAL SECURITY RISK")
            
            # Check for common weak secrets
            weak_secrets = ['secret', 'password', '123456', 'admin', 'test']
            if secret.lower() in weak_secrets:
                issues.append("JWT secret key is using a weak/common value")
            
            # Check entropy
            if self._calculate_entropy(secret) < 3.0:
                issues.append("JWT secret key has low entropy (predictable)")
        else:
            issues.append("JWT_SECRET_KEY not configured")
        
        # Check JWT algorithm
        if hasattr(settings, 'JWT_ALGORITHM'):
            if settings.JWT_ALGORITHM not in ['HS256', 'HS384', 'HS512']:
                issues.append(f"JWT algorithm {settings.JWT_ALGORITHM} may not be secure")
        
        # Check JWT expiration
        if hasattr(settings, 'JWT_EXPIRATION_HOURS'):
            if settings.JWT_EXPIRATION_HOURS > 168:  # 1 week
                issues.append("JWT expiration time is too long (security risk for token theft)")
        
        return issues
    
    def _validate_database_config(self) -> List[str]:
        """Validate database security configuration"""
        issues = []
        
        if hasattr(settings, 'DATABASE_URL'):
            db_url = settings.DATABASE_URL
            
            # Check for default credentials
            if 'arcadia_user:arcadia_pass' in db_url:
                issues.append("Database is using default credentials - change in production")
            
            # Check for localhost in production
            if settings.ENVIRONMENT == 'production' and 'localhost' in db_url:
                issues.append("Database URL contains localhost in production environment")
            
            # Check for unencrypted connections
            if 'sslmode=disable' in db_url or ('sslmode' not in db_url and 'production' in settings.ENVIRONMENT):
                issues.append("Database connection may not be using SSL encryption")
        
        return issues
    
    def _validate_environment_config(self) -> List[str]:
        """Validate environment security settings"""
        issues = []
        
        # Check environment setting
        if settings.ENVIRONMENT == 'development' and os.getenv('PRODUCTION'):
            issues.append("Environment set to development but production flag detected")
        
        # Check for debug settings in production
        if settings.ENVIRONMENT == 'production':
            if os.getenv('DEBUG', 'False').lower() == 'true':
                issues.append("Debug mode enabled in production environment")
        
        # Check log level
        if hasattr(settings, 'LOG_LEVEL'):
            if settings.LOG_LEVEL == 'DEBUG' and settings.ENVIRONMENT == 'production':
                issues.append("Debug logging enabled in production (may leak sensitive info)")
        
        return issues
    
    def _validate_file_permissions(self) -> List[str]:
        """Validate file permissions for security"""
        issues = []
        
        try:
            # Check .env file permissions
            env_file = Path('.env')
            if env_file.exists():
                stat_info = env_file.stat()
                # Check if file is readable by others
                if stat_info.st_mode & 0o044:  # Check for group/other read permissions
                    issues.append(".env file has overly permissive permissions (should be 600)")
            
            # Check logs directory permissions
            log_dir = Path('logs')
            if log_dir.exists():
                stat_info = log_dir.stat()
                if stat_info.st_mode & 0o022:  # Check for group/other write permissions
                    issues.append("Logs directory has overly permissive permissions")
        
        except Exception as e:
            # File permission checks may not work on all systems
            pass
        
        return issues
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of a string"""
        if not text:
            return 0
        
        entropy = 0
        char_counts = {}
        
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        text_len = len(text)
        for count in char_counts.values():
            probability = count / text_len
            if probability > 0:
                entropy -= probability * (probability.bit_length() - 1)
        
        return entropy

class ThreatDetector:
    """
    Runtime threat detection and monitoring
    Implements detection for the misuse cases from the project document
    """
    
    def __init__(self):
        self.suspicious_activities = []
        self.rate_limits = {}
        self.failed_attempts = {}
    
    def detect_bot_farming(self, user_id: str, game_id: str, session_duration: int, score: int) -> bool:
        """
        Detect potential bot farming activity (MS.01 from document)
        Returns True if suspicious activity detected
        """
        # Check for unrealistically short sessions with high scores
        if session_duration < 5 and score > 1000:
            self._log_suspicious_activity("BOT_FARMING_SUSPECTED", {
                "user_id": user_id,
                "game_id": game_id,
                "duration": session_duration,
                "score": score,
                "reason": "unrealistic_performance"
            })
            return True
        
        # Check for repetitive play patterns
        current_time = time.time()
        key = f"{user_id}_{game_id}"
        
        if key not in self.rate_limits:
            self.rate_limits[key] = []
        
        # Clean old entries (older than 1 hour)
        self.rate_limits[key] = [
            timestamp for timestamp in self.rate_limits[key]
            if current_time - timestamp < 3600
        ]
        
        # Add current session
        self.rate_limits[key].append(current_time)
        
        # Check if too many sessions in short time
        if len(self.rate_limits[key]) > 20:  # More than 20 sessions per hour
            self._log_suspicious_activity("BOT_FARMING_SUSPECTED", {
                "user_id": user_id,
                "game_id": game_id,
                "sessions_per_hour": len(self.rate_limits[key]),
                "reason": "excessive_play_rate"
            })
            return True
        
        return False
    
    def detect_phishing_attempt(self, email: str, user_agent: str, ip_address: str) -> bool:
        """
        Detect potential phishing attempts (MS.02 from document)
        Returns True if suspicious login detected
        """
        suspicious_indicators = []
        
        # Check for suspicious email patterns
        if re.search(r'[0-9]{3,}', email):  # Many numbers in email
            suspicious_indicators.append("suspicious_email_pattern")
        
        # Check for suspicious user agents
        bot_patterns = [
            r'bot', r'crawl', r'spider', r'scrape', r'automated',
            r'python', r'curl', r'wget', r'postman'
        ]
        
        for pattern in bot_patterns:
            if re.search(pattern, user_agent.lower()):
                suspicious_indicators.append("automated_user_agent")
                break
        
        # Log if suspicious
        if suspicious_indicators:
            self._log_suspicious_activity("PHISHING_ATTEMPT_SUSPECTED", {
                "email": email,
                "user_agent": user_agent,
                "ip_address": ip_address,
                "indicators": suspicious_indicators
            })
            return True
        
        return False
    
    def detect_cheating(self, user_id: str, game_id: str, score: int, game_difficulty: int) -> bool:
        """
        Detect potential cheating (MS.07 from document)
        Returns True if impossible scores detected
        """
        # Define theoretical maximum scores based on difficulty
        max_scores = {
            1: 2000,   # Easy games
            2: 5000,   # Medium games
            3: 10000,  # Hard games
            4: 20000,  # Very hard games
            5: 50000   # Expert games
        }
        
        max_possible = max_scores.get(game_difficulty, 10000)
        
        if score > max_possible:
            self._log_suspicious_activity("CHEATING_SUSPECTED", {
                "user_id": user_id,
                "game_id": game_id,
                "score": score,
                "max_possible": max_possible,
                "difficulty": game_difficulty,
                "reason": "impossible_score"
            })
            return True
        
        return False
    
    def detect_abuse_pattern(self, user_id: str, action: str, resource_id: str = None) -> bool:
        """
        Detect general abuse patterns
        Returns True if abuse detected
        """
        current_time = time.time()
        key = f"{user_id}_{action}"
        
        if key not in self.rate_limits:
            self.rate_limits[key] = []
        
        # Clean old entries (older than 10 minutes)
        self.rate_limits[key] = [
            timestamp for timestamp in self.rate_limits[key]
            if current_time - timestamp < 600
        ]
        
        # Add current action
        self.rate_limits[key].append(current_time)
        
        # Define rate limits per action type
        limits = {
            "login_attempt": 10,
            "game_start": 30,
            "token_purchase": 5,
            "profile_update": 10,
            "password_change": 3
        }
        
        limit = limits.get(action, 20)  # Default limit
        
        if len(self.rate_limits[key]) > limit:
            self._log_suspicious_activity("ABUSE_PATTERN_DETECTED", {
                "user_id": user_id,
                "action": action,
                "resource_id": resource_id,
                "attempts": len(self.rate_limits[key]),
                "limit": limit,
                "reason": "rate_limit_exceeded"
            })
            return True
        
        return False
    
    def _log_suspicious_activity(self, activity_type: str, details: Dict):
        """Log suspicious activity for review"""
        activity = {
            "timestamp": datetime.now(timezone.utc),
            "type": activity_type,
            "details": details
        }
        
        self.suspicious_activities.append(activity)
        
        # In a real system, this would be sent to a security monitoring service
        print(f"🚨 SECURITY ALERT: {activity_type}")
        print(f"   Details: {details}")
    
    def get_security_report(self) -> Dict:
        """Generate security report of detected threats"""
        report = {
            "total_incidents": len(self.suspicious_activities),
            "incident_types": {},
            "recent_incidents": [],
            "generated_at": datetime.now(timezone.utc)
        }
        
        # Count incident types
        for activity in self.suspicious_activities:
            activity_type = activity["type"]
            report["incident_types"][activity_type] = report["incident_types"].get(activity_type, 0) + 1
        
        # Get recent incidents (last 24 hours)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        report["recent_incidents"] = [
            activity for activity in self.suspicious_activities
            if activity["timestamp"] > cutoff
        ]
        
        return report

class InputValidator:
    """
    Input validation utilities for security
    Prevents injection attacks and validates user input
    """
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email format and security"""
        if not email or len(email) > 255:
            return False, "Email length invalid"
        
        # Basic email regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        
        # Check for suspicious patterns
        if '..' in email or email.startswith('.') or email.endswith('.'):
            return False, "Email contains suspicious patterns"
        
        return True, "Email is valid"
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """Validate username format and security"""
        if not username or len(username) < 3 or len(username) > 50:
            return False, "Username must be 3-50 characters"
        
        # Allow only alphanumeric and underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'admin', r'root', r'system', r'test', r'guest',
            r'null', r'undefined', r'script', r'select', r'drop'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, username.lower()):
                return False, f"Username contains restricted word: {pattern}"
        
        return True, "Username is valid"
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 1000) -> str:
        """Sanitize user input to prevent injection attacks"""
        if not text:
            return ""
        
        # Truncate to max length
        text = text[:max_length]
        
        # Remove or escape dangerous characters
        # This is a basic implementation - use proper libraries in production
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
        for char in dangerous_chars:
            text = text.replace(char, '')
        
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\t\n\r')
        
        return text.strip()

def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    return secrets.token_urlsafe(length)

def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for logging without exposing actual values"""
    return hashlib.sha256(data.encode()).hexdigest()[:16]

# Global instances
security_validator = SecurityValidator()
threat_detector = ThreatDetector()
input_validator = InputValidator()

if __name__ == "__main__":
    # Allow running security checks directly
    print("🔒 Running security validation...")
    
    validator = SecurityValidator()
    issues = validator.validate_configuration()
    
    if issues:
        print("\n⚠️  Security issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print("\n💡 Please address these issues before production deployment")
    else:
        print("✅ No security issues found in configuration")
    
    # Show threat detection status
    detector = ThreatDetector()
    report = detector.get_security_report()
    print(f"\n📊 Security monitoring active")
    print(f"   Total incidents tracked: {report['total_incidents']}")