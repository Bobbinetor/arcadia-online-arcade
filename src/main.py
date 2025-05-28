#!/usr/bin/env python3
"""
Arcadia Online Arcade Platform - Main Entry Point
Terminal-based first release implementing secure authentication and game mechanics
"""
import sys
import os
import time
import logging
from pathlib import Path
from sqlalchemy import text

# Configure logging to suppress verbose SQLAlchemy logs
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARNING)

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "src"))
sys.path.append(str(PROJECT_ROOT / "config"))

# Import configuration first
try:
    from config.settings import settings
    print(f"✅ Configuration loaded - Environment: {settings.ENVIRONMENT}")
except ImportError as e:
    print(f"❌ Failed to load configuration: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

# Import core services
try:
    from models.database import db_manager
    from services.auth_service import auth_service
    from services.game_service import game_service
    from cli.menu_cli import ArcadiaTerminal
    from utils.database_utils import DatabaseInitializer
    from utils.security_utils import SecurityValidator
except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    print("Make sure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)

def check_dependencies():
    """Check if all required dependencies are available"""
    required_modules = [
        'psycopg2', 'sqlalchemy', 'bcrypt', 'jwt', 
        'colorama', 'rich', 'click', 'dotenv'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module.replace('-', '_'))
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ Missing required dependencies: {', '.join(missing_modules)}")
        print("Install them with: pip install -r requirements.txt")
        return False
    
    return True

def check_database_connection():
    """Check database connection and initialize if needed"""
    try:
        print("🔍 Checking database connection...")
        
        # Test connection
        session = db_manager.get_session()
        session.execute(text("SELECT 1"))
        session.close()
        
        print("✅ Database connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure PostgreSQL is running: docker-compose up -d")
        print("2. Check your .env file database configuration")
        print("3. Verify the database exists and credentials are correct")
        return False

def initialize_database():
    """Initialize database with tables and sample data"""
    try:
        print("🗄️  Initializing database...")
        
        # Create tables
        db_manager.create_tables()
        
        # Initialize with sample data if needed
        initializer = DatabaseInitializer()
        initializer.ensure_sample_data()
        
        print("✅ Database initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def run_security_checks():
    """Run basic security validation"""
    try:
        print("🔒 Running security checks...")
        
        validator = SecurityValidator()
        issues = validator.validate_configuration()
        
        if issues:
            print("⚠️  Security issues found:")
            for issue in issues:
                print(f"   - {issue}")
            print("\n💡 Fix these issues before production deployment")
        else:
            print("✅ Basic security checks passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Security check failed: {e}")
        return False

def print_startup_banner():
    """Print application startup banner"""
    banner = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                         🎮 ARCADIA PLATFORM 🎮                              ║
║                     Terminal Release v{settings.APP_VERSION}                           ║
║                                                                              ║
║  Welcome to the secure, terminal-based arcade gaming platform!              ║
║  Features: JWT Authentication, Token Economy, Creator Tools                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)

def main():
    """Main application entry point"""
    try:
        print_startup_banner()
        
        # Pre-flight checks
        print("🚀 Starting Arcadia Platform...")
        print(f"📍 Project root: {PROJECT_ROOT}")
        print(f"🌍 Environment: {settings.ENVIRONMENT}")
        
        # Check dependencies
        if not check_dependencies():
            sys.exit(1)
        
        # Check database connection
        if not check_database_connection():
            print("\n❓ Would you like to:")
            print("1. Try to start the database with docker-compose")
            print("2. Exit and fix manually")
            
            choice = input("Enter choice (1/2): ").strip()
            if choice == "1":
                print("\n🐳 Attempting to start database...")
                import subprocess
                try:
                    subprocess.run(["docker-compose", "up", "-d", "postgres"], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"❌ Failed to start database: {e}")
                    sys.exit(1)
                time.sleep(5)  # Wait for database to start
                
                if not check_database_connection():
                    print("❌ Still cannot connect to database. Please check manually.")
                    sys.exit(1)
            else:
                sys.exit(1)
        
        # Initialize database
        if not initialize_database():
            sys.exit(1)
        
        # Run security checks
        run_security_checks()
        
        print("\n🎉 All systems ready! Starting Arcadia Terminal...")
        time.sleep(1)
        
        # Start the terminal interface
        terminal = ArcadiaTerminal()
        terminal.run()
        
    except KeyboardInterrupt:
        print("\n\n👋 Arcadia Platform shutdown requested by user")
        print("Thanks for using Arcadia! Goodbye!")
        
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        print("Please check the logs and try again")
        sys.exit(1)
    
    finally:
        print("\n🔒 Shutting down Arcadia Platform...")
        print("✅ Cleanup complete. See you next time!")

if __name__ == "__main__":
    main()