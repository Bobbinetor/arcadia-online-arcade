"""
Game Service for Arcadia Platform
Handles game mechanics, token economy, and creator revenue system
"""
import uuid
import random
import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config'))

# Try importing settings with fallback
try:
    from settings import settings
except ImportError:
    # Fallback settings class
    class FallbackSettings:
        CREATOR_REVENUE_SHARE = 0.35
        DEFAULT_TOKENS = 100
    settings = FallbackSettings()

from models.database import User, Game, GameSession, Transaction, Achievement, AuditLog, db_manager

class InsufficientTokensError(Exception):
    """Raised when user doesn't have enough tokens"""
    pass

class GameNotFoundError(Exception):
    """Raised when game is not found or not available"""
    pass

class GameService:
    """
    Game service implementing the arcade game mechanics and economy
    Features:
    - Token-based game access system
    - Creator revenue sharing (30-50% as per document)
    - Game session tracking
    - Achievement system
    - Leaderboards
    """
    
    def __init__(self):
        self.creator_revenue_share = settings.CREATOR_REVENUE_SHARE
    
    def _log_audit_event(self, session: Session, action: str, user_id: Optional[uuid.UUID] = None, 
                        details: Dict = None, severity: str = "INFO"):
        """Log game-related audit events"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type="game",
                details=details or {},
                severity=severity
            )
            session.add(audit_log)
            session.flush()
        except Exception as e:
            print(f"Warning: Failed to log audit event: {e}")
    
    def _create_transaction(self, session: Session, user_id: uuid.UUID, transaction_type: str,
                          amount: Decimal, tokens_involved: int = 0, description: str = "",
                          reference_id: Optional[uuid.UUID] = None):
        """Create a financial transaction record"""
        transaction = Transaction(
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            tokens_involved=tokens_involved,
            description=description,
            reference_id=reference_id
        )
        session.add(transaction)
        return transaction
    
    def _award_achievement(self, session: Session, user_id: uuid.UUID, achievement_type: str,
                          achievement_name: str, description: str, achievement_data: Dict = None):
        """Award an achievement to a user"""
        # Check if user already has this achievement
        existing = session.query(Achievement).filter(
            Achievement.user_id == user_id,
            Achievement.achievement_type == achievement_type
        ).first()
        
        if not existing:
            achievement = Achievement(
                user_id=user_id,
                achievement_type=achievement_type,
                achievement_name=achievement_name,
                description=description,
                achievement_data=achievement_data or {}
            )
            session.add(achievement)
            return achievement
        return None
    
    def get_available_games(self, user: User) -> List[Dict]:
        """
        Get list of available games for the user
        Considers subscription status and token balance
        """
        session = db_manager.get_session()
        
        try:
            games = session.query(Game).filter(Game.is_active == True).all()
            available_games = []
            
            for game in games:
                can_play = False
                reason = ""
                
                if game.game_type == "free_to_play":
                    can_play = True
                elif game.game_type == "premium":
                    if user.subscription_active and (
                        user.subscription_expires_at is None or 
                        user.subscription_expires_at > datetime.now(timezone.utc)
                    ):
                        can_play = True
                        reason = "Available with subscription"
                    elif user.tokens >= game.token_cost:
                        can_play = True
                        reason = f"Costs {game.token_cost} tokens"
                    else:
                        reason = f"Need {game.token_cost} tokens (you have {user.tokens})"
                elif game.game_type == "user_created":
                    if user.tokens >= game.token_cost:
                        can_play = True
                        reason = f"Community game - {game.token_cost} tokens"
                    else:
                        reason = f"Need {game.token_cost} tokens"
                
                game_info = {
                    "id": str(game.id),
                    "title": game.title,
                    "description": game.description,
                    "type": game.game_type,
                    "token_cost": game.token_cost,
                    "difficulty": game.difficulty_level,
                    "play_count": game.play_count,
                    "max_score": game.max_score,
                    "can_play": can_play,
                    "reason": reason,
                    "creator": game.creator.username if game.creator else "Arcadia"
                }
                available_games.append(game_info)
            
            return available_games
            
        finally:
            session.close()
    
    def start_game_session(self, user_id: uuid.UUID, game_id: uuid.UUID) -> Tuple[bool, str, Optional[Dict]]:
        """
        Start a new game session
        Implements token deduction and access control (US.M.02, US.A.01)
        """
        session = db_manager.get_session()
        
        try:
            # Get user and game
            user = session.query(User).filter(User.id == user_id, User.is_active == True).first()
            game = session.query(Game).filter(Game.id == game_id, Game.is_active == True).first()
            
            if not user:
                return False, "User not found", None
            
            if not game:
                return False, "Game not found", None
            
            tokens_to_spend = 0
            
            # Check access permissions
            if game.game_type == "free_to_play":
                tokens_to_spend = 0
            elif game.game_type == "premium":
                # Check subscription first
                if user.subscription_active and (
                    user.subscription_expires_at is None or 
                    user.subscription_expires_at > datetime.now(timezone.utc)
                ):
                    tokens_to_spend = 0
                else:
                    # Pay with tokens
                    tokens_to_spend = game.token_cost
                    if user.tokens < tokens_to_spend:
                        return False, f"Insufficient tokens. Need {tokens_to_spend}, have {user.tokens}", None
            elif game.game_type == "user_created":
                tokens_to_spend = game.token_cost
                if user.tokens < tokens_to_spend:
                    return False, f"Insufficient tokens. Need {tokens_to_spend}, have {user.tokens}", None
            
            # Deduct tokens if needed
            if tokens_to_spend > 0:
                user.tokens -= tokens_to_spend
                
                # Create transaction record
                self._create_transaction(
                    session, user_id, "game_play", 
                    Decimal(str(tokens_to_spend * 0.01)),  # Assuming 1 token = $0.01
                    tokens_to_spend,
                    f"Playing {game.title}",
                    game_id
                )
            
            # Create game session
            game_session = GameSession(
                user_id=user_id,
                game_id=game_id,
                tokens_spent=tokens_to_spend
            )
            session.add(game_session)
            session.flush()
            
            # Update game play count
            game.play_count += 1
            
            # Process creator revenue if applicable
            if tokens_to_spend > 0 and game.creator_id and game.creator_id != user_id:
                creator_revenue = int(tokens_to_spend * self.creator_revenue_share)
                if creator_revenue > 0:
                    creator = session.query(User).filter(User.id == game.creator_id).first()
                    if creator:
                        creator.tokens += creator_revenue
                        game.revenue_generated += Decimal(str(creator_revenue * 0.01))
                        
                        # Create creator payout transaction
                        self._create_transaction(
                            session, game.creator_id, "creator_payout",
                            Decimal(str(creator_revenue * 0.01)),
                            creator_revenue,
                            f"Revenue from {game.title} played by {user.username}",
                            game_session.id
                        )
            
            # Log the event
            self._log_audit_event(session, "GAME_SESSION_STARTED", user_id, {
                "game_id": str(game_id),
                "game_title": game.title,
                "tokens_spent": tokens_to_spend,
                "session_id": str(game_session.id)
            })
            
            session.commit()
            
            session_info = {
                "session_id": str(game_session.id),
                "game_title": game.title,
                "tokens_spent": tokens_to_spend,
                "remaining_tokens": user.tokens,
                "difficulty": game.difficulty_level
            }
            
            return True, "Game session started successfully", session_info
            
        except Exception as e:
            session.rollback()
            self._log_audit_event(session, "GAME_SESSION_START_ERROR", user_id, {
                "game_id": str(game_id),
                "error": str(e)
            }, "ERROR")
            return False, f"Failed to start game: {str(e)}", None
        finally:
            session.close()
    
    def simulate_game_play(self, session_id: uuid.UUID, difficulty: int = 1) -> Dict:
        """
        Simulate a simple arcade game for the terminal interface
        Returns game results and score
        """
        # Simple game simulation based on difficulty
        # Note: Using standard random for game mechanics (not security-sensitive)
        base_score = random.randint(100, 1000)  # nosec B311
        multiplier = 1 + (difficulty * 0.5)
        final_score = int(base_score * multiplier)
        
        # Simulate game duration (10-60 seconds based on difficulty)
        duration = random.randint(10 + difficulty * 5, 30 + difficulty * 10)  # nosec B311
        
        # Random events during gameplay
        events = [
            "Game started!",
            "Power-up collected!",
            "Bonus points earned!",
            "Near miss!",
            "Perfect combo!",
            "Game over!"
        ]
        
        # Determine if completed (higher difficulty = lower completion rate)
        completion_chance = max(0.3, 0.9 - (difficulty * 0.15))
        completed = random.random() < completion_chance  # nosec B311
        
        return {
            "score": final_score,
            "duration": duration,
            "completed": completed,
            "events": random.sample(events[:-1], min(3, len(events)-1)) + [events[-1]]  # nosec B311
        }
    
    def end_game_session(self, session_id: uuid.UUID, score: int, duration: int, 
                        completed: bool = False) -> Tuple[bool, str, List[str]]:
        """
        End a game session and record results
        Awards achievements and updates high scores
        """
        session = db_manager.get_session()
        achievements_earned = []
        
        try:
            # Get game session
            game_session = session.query(GameSession).filter(GameSession.id == session_id).first()
            if not game_session:
                return False, "Game session not found", []
            
            # Update session results
            game_session.score = score
            game_session.duration_seconds = duration
            game_session.completed = completed
            
            # Get game and user for achievement checking
            game = session.query(Game).filter(Game.id == game_session.game_id).first()
            user = session.query(User).filter(User.id == game_session.user_id).first()
            
            # Update game high score
            if score > game.max_score:
                game.max_score = score
                
                # Award high score achievement
                achievement = self._award_achievement(
                    session, user.id, "high_score",
                    "New High Score!", 
                    f"Set new high score in {game.title}",
                    {"game": game.title, "score": score}
                )
                if achievement:
                    achievements_earned.append("🏆 New High Score!")
            
            # Check for other achievements
            user_sessions = session.query(GameSession).filter(GameSession.user_id == user.id).count()
            
            # First game achievement
            if user_sessions == 1:
                achievement = self._award_achievement(
                    session, user.id, "first_game",
                    "Welcome to Arcadia!",
                    "Played your first game"
                )
                if achievement:
                    achievements_earned.append("🎮 Welcome to Arcadia!")
            
            # Games milestone achievements
            milestones = [10, 50, 100, 500]
            for milestone in milestones:
                if user_sessions == milestone:
                    achievement = self._award_achievement(
                        session, user.id, "games_played",
                        f"Arcade Veteran - {milestone} Games",
                        f"Played {milestone} games"
                    )
                    if achievement:
                        achievements_earned.append(f"🎯 Played {milestone} games!")
            
            # Perfect score achievement
            if completed and score >= 1000:
                achievement = self._award_achievement(
                    session, user.id, "perfect_game",
                    "Perfect Game!",
                    f"Completed {game.title} with high score"
                )
                if achievement:
                    achievements_earned.append("⭐ Perfect Game!")
            
            # Log session completion
            self._log_audit_event(session, "GAME_SESSION_COMPLETED", user.id, {
                "session_id": str(session_id),
                "game_title": game.title,
                "score": score,
                "duration": duration,
                "completed": completed,
                "achievements": len(achievements_earned)
            })
            
            session.commit()
            
            return True, "Game session completed successfully", achievements_earned
            
        except Exception as e:
            session.rollback()
            self._log_audit_event(session, "GAME_SESSION_END_ERROR", None, {
                "session_id": str(session_id),
                "error": str(e)
            }, "ERROR")
            return False, f"Failed to end game session: {str(e)}", []
        finally:
            session.close()
    
    def get_leaderboard(self, game_id: Optional[uuid.UUID] = None, limit: int = 10) -> List[Dict]:
        """
        Get leaderboard for a specific game or global leaderboard
        Implements competitive features for Marco "Il Competitivo" persona
        """
        session = db_manager.get_session()
        
        try:
            query = session.query(
                GameSession.score,
                User.username,
                Game.title,
                GameSession.created_at
            ).join(User, GameSession.user_id == User.id).join(Game, GameSession.game_id == Game.id)
            
            if game_id:
                query = query.filter(GameSession.game_id == game_id)
            
            results = query.order_by(desc(GameSession.score)).limit(limit).all()
            
            leaderboard = []
            for i, (score, username, game_title, created_at) in enumerate(results, 1):
                # Handle both datetime objects and string dates
                if hasattr(created_at, 'strftime'):
                    date_str = created_at.strftime("%Y-%m-%d")
                else:
                    date_str = str(created_at)
                
                leaderboard.append({
                    "rank": i,
                    "username": username,
                    "score": score,
                    "game": game_title,
                    "date": date_str
                })
            
            return leaderboard
            
        finally:
            session.close()
    
    def get_user_statistics(self, user_id: uuid.UUID) -> Dict:
        """
        Get comprehensive user gaming statistics
        Supports profile dashboard (US.X.02)
        """
        session = db_manager.get_session()
        
        try:
            # Basic stats
            total_sessions = session.query(GameSession).filter(GameSession.user_id == user_id).count()
            total_score = session.query(func.sum(GameSession.score)).filter(GameSession.user_id == user_id).scalar() or 0
            total_tokens_spent = session.query(func.sum(GameSession.tokens_spent)).filter(GameSession.user_id == user_id).scalar() or 0
            completed_games = session.query(GameSession).filter(
                GameSession.user_id == user_id,
                GameSession.completed == True
            ).count()
            
            # Achievements
            achievements = session.query(Achievement).filter(Achievement.user_id == user_id).count()
            
            # Best scores per game
            best_scores = session.query(
                Game.title,
                func.max(GameSession.score).label('best_score')
            ).join(GameSession).filter(GameSession.user_id == user_id).group_by(Game.title).all()
            
            # Games created (if user is a creator)
            games_created = session.query(Game).filter(Game.creator_id == user_id).count()
            total_revenue = session.query(func.sum(Game.revenue_generated)).filter(Game.creator_id == user_id).scalar() or 0
            
            return {
                "total_games_played": total_sessions,
                "total_score": total_score,
                "total_tokens_spent": total_tokens_spent,
                "completed_games": completed_games,
                "completion_rate": round((completed_games / total_sessions * 100) if total_sessions > 0 else 0, 1),
                "achievements_earned": achievements,
                "games_created": games_created,
                "creator_revenue": float(total_revenue),
                "best_scores": [{"game": title, "score": score} for title, score in best_scores]
            }
            
        finally:
            session.close()
    
    def purchase_tokens(self, user_id: uuid.UUID, token_amount: int, payment_amount: float) -> Tuple[bool, str]:
        """
        Purchase tokens for the user
        Implements token economy (US.M.02)
        """
        session = db_manager.get_session()
        
        try:
            user = session.query(User).filter(User.id == user_id, User.is_active == True).first()
            if not user:
                return False, "User not found"
            
            # Add tokens to user account
            user.tokens += token_amount
            
            # Create transaction record
            self._create_transaction(
                session, user_id, "token_purchase",
                Decimal(str(payment_amount)),
                token_amount,
                f"Purchased {token_amount} tokens"
            )
            
            # Log the purchase
            self._log_audit_event(session, "TOKENS_PURCHASED", user_id, {
                "tokens_purchased": token_amount,
                "amount_paid": payment_amount,
                "new_balance": user.tokens
            })
            
            session.commit()
            return True, f"Successfully purchased {token_amount} tokens"
            
        except Exception as e:
            session.rollback()
            return False, f"Token purchase failed: {str(e)}"
        finally:
            session.close()

# Global game service instance
game_service = GameService()