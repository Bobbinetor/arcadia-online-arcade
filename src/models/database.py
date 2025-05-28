"""
Database models and connection management for Arcadia Platform
"""
from sqlalchemy import create_engine, Column, String, Integer, Boolean, TIMESTAMP, DECIMAL, Text, ForeignKey, Index
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import Optional
import sys
import os

# Add the config directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config'))

# Try importing settings with fallback
try:
    from settings import settings
except ImportError:
    # Fallback settings class
    class FallbackSettings:
        DATABASE_URL = "postgresql://arcadia_user:arcadia_pass@localhost:5432/arcadia"
        DEFAULT_TOKENS = 100
        ENVIRONMENT = "development"
        
        @classmethod
        def get_database_url(cls):
            return cls.DATABASE_URL
    settings = FallbackSettings()

Base = declarative_base()

class User(Base):
    """User model for authentication and profile management"""
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    tokens = Column(Integer, default=settings.DEFAULT_TOKENS)
    subscription_active = Column(Boolean, default=False)
    subscription_expires_at = Column(TIMESTAMP)
    profile_data = Column(JSONB, default={})
    created_at = Column(TIMESTAMP, default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, default=func.current_timestamp(), onupdate=func.current_timestamp())
    last_login = Column(TIMESTAMP)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    games = relationship("Game", back_populates="creator")
    sessions = relationship("GameSession", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    achievements = relationship("Achievement", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"

class Game(Base):
    """Game model for arcade game library"""
    __tablename__ = 'games'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    creator_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    game_type = Column(String(50), nullable=False)  # 'premium', 'free_to_play', 'user_created'
    token_cost = Column(Integer, default=0)
    difficulty_level = Column(Integer, default=1)
    max_score = Column(Integer, default=0)
    play_count = Column(Integer, default=0)
    revenue_generated = Column(DECIMAL(10, 2), default=0.00)
    game_data = Column(JSONB, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    creator = relationship("User", back_populates="games")
    sessions = relationship("GameSession", back_populates="game")
    
    # Indexes
    __table_args__ = (
        Index('idx_games_creator', 'creator_id'),
        Index('idx_games_type', 'game_type'),
    )
    
    def __repr__(self):
        return f"<Game(title='{self.title}', type='{self.game_type}')>"

class GameSession(Base):
    """Game session model for tracking gameplay"""
    __tablename__ = 'game_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    game_id = Column(UUID(as_uuid=True), ForeignKey('games.id', ondelete='CASCADE'))
    score = Column(Integer, default=0)
    tokens_spent = Column(Integer, default=0)
    duration_seconds = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    session_data = Column(JSONB, default={})
    created_at = Column(TIMESTAMP, default=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    game = relationship("Game", back_populates="sessions")
    
    # Indexes
    __table_args__ = (
        Index('idx_sessions_user', 'user_id'),
        Index('idx_sessions_game', 'game_id'),
    )
    
    def __repr__(self):
        return f"<GameSession(user_id='{self.user_id}', game_id='{self.game_id}', score={self.score})>"

class Transaction(Base):
    """Transaction model for financial tracking"""
    __tablename__ = 'transactions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    transaction_type = Column(String(50), nullable=False)  # 'token_purchase', 'game_play', 'creator_payout', 'subscription'
    amount = Column(DECIMAL(10, 2), nullable=False)
    tokens_involved = Column(Integer, default=0)
    description = Column(Text)
    reference_id = Column(UUID(as_uuid=True))  # Can reference game_id, session_id, etc.
    status = Column(String(20), default='completed')
    created_at = Column(TIMESTAMP, default=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    
    # Indexes
    __table_args__ = (
        Index('idx_transactions_user', 'user_id'),
        Index('idx_transactions_type', 'transaction_type'),
    )
    
    def __repr__(self):
        return f"<Transaction(type='{self.transaction_type}', amount={self.amount})>"

class Achievement(Base):
    """Achievement model for user badges and trophies"""
    __tablename__ = 'achievements'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    achievement_type = Column(String(100), nullable=False)
    achievement_name = Column(String(255), nullable=False)
    description = Column(Text)
    earned_at = Column(TIMESTAMP, default=func.current_timestamp())
    achievement_data = Column(JSONB, default={})
    
    # Relationships
    user = relationship("User", back_populates="achievements")
    
    def __repr__(self):
        return f"<Achievement(name='{self.achievement_name}', user_id='{self.user_id}')>"

class AuditLog(Base):
    """Audit log model for security and monitoring"""
    __tablename__ = 'audit_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(UUID(as_uuid=True))
    ip_address = Column(INET)
    user_agent = Column(Text)
    details = Column(JSONB, default={})
    severity = Column(String(20), default='INFO')
    created_at = Column(TIMESTAMP, default=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_timestamp', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AuditLog(action='{self.action}', severity='{self.severity}')>"

class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection"""
        try:
            self.engine = create_engine(
                settings.get_database_url(),
                echo=False,  # Disable SQL logging for cleaner terminal output
                pool_pre_ping=True,
                pool_recycle=300
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            print(f"✅ Database connection established")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise
    
    def create_tables(self):
        """Create all tables if they don't exist"""
        try:
            Base.metadata.create_all(bind=self.engine)
            print("✅ Database tables created successfully")
        except Exception as e:
            print(f"❌ Failed to create tables: {e}")
            raise
    
    def get_session(self):
        """Get a new database session"""
        session = self.SessionLocal()
        try:
            return session
        except Exception as e:
            session.close()
            raise e
    
    def close_session(self, session):
        """Close a database session"""
        try:
            session.close()
        except Exception as e:
            print(f"Warning: Error closing session: {e}")

# Global database manager instance
db_manager = DatabaseManager()

def get_db_session():
    """Dependency to get database session"""
    session = db_manager.get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)