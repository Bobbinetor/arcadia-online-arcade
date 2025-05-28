"""
Database Utilities for Arcadia Platform
Handles database initialization, sample data creation, and maintenance tasks
"""
import uuid
import sys
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Dict
from sqlalchemy.exc import IntegrityError

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config'))

from models.database import (
    db_manager, User, Game, GameSession, Transaction, 
    Achievement, AuditLog
)
from services.auth_service import auth_service

# Try importing settings with fallback
try:
    from settings import settings
except ImportError:
    # Fallback settings class
    class FallbackSettings:
        DEFAULT_TOKENS = 100
    settings = FallbackSettings()

class DatabaseInitializer:
    """
    Database initialization and sample data management
    Ensures the platform has initial content for testing and demonstration
    """
    
    def __init__(self):
        self.sample_games_data = [
            {
                "title": "Pixel Snake",
                "description": "Classic snake game with retro pixel graphics. Collect dots and grow your snake!",
                "game_type": "free_to_play",
                "token_cost": 0,
                "difficulty_level": 1,
                "game_data": {
                    "category": "arcade_classic",
                    "controls": "arrow_keys",
                    "max_players": 1
                }
            },
            {
                "title": "Space Invaders Classic",
                "description": "Defend Earth from waves of alien invaders in this timeless arcade shooter.",
                "game_type": "premium",
                "token_cost": 2,
                "difficulty_level": 2,
                "game_data": {
                    "category": "shooter",
                    "controls": "arrow_keys_space",
                    "max_players": 1
                }
            },
            {
                "title": "Tetris Challenge",
                "description": "Stack falling blocks to clear lines in this puzzle classic.",
                "game_type": "premium",
                "token_cost": 3,
                "difficulty_level": 3,
                "game_data": {
                    "category": "puzzle",
                    "controls": "arrow_keys",
                    "max_players": 1
                }
            },
            {
                "title": "Pac-Man Adventure",
                "description": "Navigate mazes, collect dots, and avoid ghosts in this legendary game.",
                "game_type": "premium",
                "token_cost": 2,
                "difficulty_level": 2,
                "game_data": {
                    "category": "maze",
                    "controls": "arrow_keys",
                    "max_players": 1
                }
            },
            {
                "title": "Breakout Master",
                "description": "Break bricks with your paddle in this addictive arcade game.",
                "game_type": "free_to_play",
                "token_cost": 1,
                "difficulty_level": 1,
                "game_data": {
                    "category": "arcade_classic",
                    "controls": "left_right_arrow",
                    "max_players": 1
                }
            },
            {
                "title": "Asteroids Shooter",
                "description": "Survive in the dangerous asteroid field and fight for the high score.",
                "game_type": "premium",
                "token_cost": 4,
                "difficulty_level": 4,
                "game_data": {
                    "category": "shooter",
                    "controls": "arrow_keys_space",
                    "max_players": 1
                }
            },
            {
                "title": "Frogger Road Cross",
                "description": "Help the frog cross busy roads and rivers safely.",
                "game_type": "free_to_play",
                "token_cost": 0,
                "difficulty_level": 2,
                "game_data": {
                    "category": "arcade_classic",
                    "controls": "arrow_keys",
                    "max_players": 1
                }
            },
            {
                "title": "Centipede Hunt",
                "description": "Shoot the descending centipede before it reaches the bottom.",
                "game_type": "premium",
                "token_cost": 3,
                "difficulty_level": 3,
                "game_data": {
                    "category": "shooter",
                    "controls": "arrow_keys_space",
                    "max_players": 1
                }
            }
        ]
    
    def ensure_sample_data(self):
        """Ensure the database has sample data for demonstration"""
        session = db_manager.get_session()
        
        try:
            # Check if we already have games
            existing_games = session.query(Game).count()
            
            if existing_games == 0:
                print("📦 Creating sample games...")
                self._create_sample_games(session)
                print(f"✅ Created {len(self.sample_games_data)} sample games")
            else:
                print(f"ℹ️  Database already contains {existing_games} games")
            
            # Create admin user if it doesn't exist
            self._ensure_admin_user(session)
            
            # Create demo user for testing
            self._ensure_demo_user(session)
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            print(f"❌ Failed to create sample data: {e}")
            raise
        finally:
            session.close()
    
    def _create_sample_games(self, session):
        """Create sample games in the database"""
        for game_data in self.sample_games_data:
            try:
                game = Game(
                    title=game_data["title"],
                    description=game_data["description"],
                    game_type=game_data["game_type"],
                    token_cost=game_data["token_cost"],
                    difficulty_level=game_data["difficulty_level"],
                    game_data=game_data["game_data"]
                )
                session.add(game)
                session.flush()  # Get the ID
                
                print(f"  ✅ Created game: {game.title}")
                
            except Exception as e:
                print(f"  ❌ Failed to create game {game_data['title']}: {e}")
                continue
    
    def _ensure_admin_user(self, session):
        """Ensure admin user exists"""
        admin_email = "admin@arcadia.local"
        
        # Check if admin user exists
        existing_admin = session.query(User).filter(User.email == admin_email).first()
        
        if not existing_admin:
            print("👤 Creating admin user...")
            # Use environment variable or generate secure password
            admin_password = os.getenv('ADMIN_PASSWORD', 'AdminArcadia2024!')  # nosec B106
            success, message, admin_user = auth_service.register_user(
                email=admin_email,
                username="ArcadiaAdmin",
                password=admin_password
            )
            
            if success:
                print(f"✅ Admin user created: {admin_email}")
                if admin_password == 'AdminArcadia2024!':
                    print(f"   Password: {admin_password}")
                    print("   ⚠️  Please change the default password!")
                else:
                    print("   Password: [Set from ADMIN_PASSWORD environment variable]")
                
                # Give admin extra tokens
                if admin_user:
                    admin_user.tokens = 1000
                    admin_user.subscription_active = True
                    admin_user.subscription_expires_at = datetime.now(timezone.utc) + timedelta(days=365)
                    session.merge(admin_user)
                    
            else:
                print(f"❌ Failed to create admin user: {message}")
        else:
            print("ℹ️  Admin user already exists")
    
    def _ensure_demo_user(self, session):
        """Ensure demo user exists for testing"""
        demo_email = "demo@arcadia.local"
        
        # Check if demo user exists
        existing_demo = session.query(User).filter(User.email == demo_email).first()
        
        if not existing_demo:
            print("👤 Creating demo user...")
            # Use environment variable or generate secure password
            demo_password = os.getenv('DEMO_PASSWORD', 'Demo123!')  # nosec B106
            success, message, demo_user = auth_service.register_user(
                email=demo_email,
                username="DemoPlayer",
                password=demo_password
            )
            
            if success:
                print(f"✅ Demo user created: {demo_email}")
                if demo_password == 'Demo123!':
                    print(f"   Password: {demo_password}")
                    print("   ⚠️  Please change the default password!")
                else:
                    print("   Password: [Set from DEMO_PASSWORD environment variable]")
                
                # Give demo user some extra tokens
                if demo_user:
                    demo_user.tokens = 200
                    session.merge(demo_user)
                    
            else:
                print(f"❌ Failed to create demo user: {message}")
        else:
            print("ℹ️  Demo user already exists")

class DatabaseMaintenance:
    """Database maintenance and cleanup utilities"""
    
    def __init__(self):
        pass
    
    def cleanup_old_sessions(self, days_old: int = 30):
        """Clean up old game sessions"""
        session = db_manager.get_session()
        
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            
            old_sessions = session.query(GameSession).filter(
                GameSession.created_at < cutoff_date
            ).count()
            
            if old_sessions > 0:
                session.query(GameSession).filter(
                    GameSession.created_at < cutoff_date
                ).delete()
                
                session.commit()
                print(f"🧹 Cleaned up {old_sessions} old game sessions")
            else:
                print("ℹ️  No old sessions to clean up")
                
        except Exception as e:
            session.rollback()
            print(f"❌ Failed to cleanup sessions: {e}")
        finally:
            session.close()
    
    def cleanup_old_audit_logs(self, days_old: int = 90):
        """Clean up old audit logs"""
        session = db_manager.get_session()
        
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            
            old_logs = session.query(AuditLog).filter(
                AuditLog.created_at < cutoff_date,
                AuditLog.severity == 'INFO'  # Keep WARNING and ERROR logs longer
            ).count()
            
            if old_logs > 0:
                session.query(AuditLog).filter(
                    AuditLog.created_at < cutoff_date,
                    AuditLog.severity == 'INFO'
                ).delete()
                
                session.commit()
                print(f"🧹 Cleaned up {old_logs} old audit logs")
            else:
                print("ℹ️  No old audit logs to clean up")
                
        except Exception as e:
            session.rollback()
            print(f"❌ Failed to cleanup audit logs: {e}")
        finally:
            session.close()
    
    def generate_database_stats(self) -> Dict:
        """Generate database statistics"""
        session = db_manager.get_session()
        
        try:
            stats = {
                "users": {
                    "total": session.query(User).count(),
                    "active": session.query(User).filter(User.is_active == True).count(),
                    "with_subscription": session.query(User).filter(User.subscription_active == True).count()
                },
                "games": {
                    "total": session.query(Game).count(),
                    "active": session.query(Game).filter(Game.is_active == True).count(),
                    "by_type": {}
                },
                "sessions": {
                    "total": session.query(GameSession).count(),
                    "completed": session.query(GameSession).filter(GameSession.completed == True).count(),
                    "today": session.query(GameSession).filter(
                        GameSession.created_at >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
                    ).count()
                },
                "transactions": {
                    "total": session.query(Transaction).count(),
                    "total_amount": session.query(Transaction).with_entities(
                        session.query(Transaction.amount).func.sum()
                    ).scalar() or 0
                },
                "achievements": {
                    "total": session.query(Achievement).count(),
                    "unique_users": session.query(Achievement.user_id).distinct().count()
                }
            }
            
            # Game types breakdown
            from sqlalchemy import func
            game_types = session.query(
                Game.game_type, 
                func.count(Game.id)
            ).group_by(Game.game_type).all()
            
            for game_type, count in game_types:
                stats["games"]["by_type"][game_type] = count
            
            return stats
            
        finally:
            session.close()
    
    def print_database_stats(self):
        """Print formatted database statistics"""
        stats = self.generate_database_stats()
        
        print("\n📊 DATABASE STATISTICS")
        print("=" * 50)
        
        print(f"\n👥 USERS:")
        print(f"   Total Users: {stats['users']['total']}")
        print(f"   Active Users: {stats['users']['active']}")
        print(f"   Subscribers: {stats['users']['with_subscription']}")
        
        print(f"\n🎮 GAMES:")
        print(f"   Total Games: {stats['games']['total']}")
        print(f"   Active Games: {stats['games']['active']}")
        for game_type, count in stats['games']['by_type'].items():
            print(f"   {game_type.replace('_', ' ').title()}: {count}")
        
        print(f"\n🎯 GAME SESSIONS:")
        print(f"   Total Sessions: {stats['sessions']['total']}")
        print(f"   Completed: {stats['sessions']['completed']}")
        print(f"   Today: {stats['sessions']['today']}")
        
        print(f"\n💰 TRANSACTIONS:")
        print(f"   Total Transactions: {stats['transactions']['total']}")
        print(f"   Total Amount: ${stats['transactions']['total_amount']:.2f}")
        
        print(f"\n🏆 ACHIEVEMENTS:")
        print(f"   Total Achievements: {stats['achievements']['total']}")
        print(f"   Users with Achievements: {stats['achievements']['unique_users']}")

def run_database_maintenance():
    """Run database maintenance tasks"""
    print("🔧 Running database maintenance...")
    
    maintenance = DatabaseMaintenance()
    
    # Clean up old data
    maintenance.cleanup_old_sessions(days_old=30)
    maintenance.cleanup_old_audit_logs(days_old=90)
    
    # Show statistics
    maintenance.print_database_stats()
    
    print("✅ Database maintenance complete")

if __name__ == "__main__":
    # Allow running maintenance directly
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "maintenance":
        run_database_maintenance()
    elif len(sys.argv) > 1 and sys.argv[1] == "init":
        initializer = DatabaseInitializer()
        initializer.ensure_sample_data()
    else:
        print("Usage:")
        print("  python database_utils.py init        - Initialize sample data")
        print("  python database_utils.py maintenance - Run maintenance tasks")