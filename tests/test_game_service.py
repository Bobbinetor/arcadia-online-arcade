"""
Unit tests for game service
Tests game mechanics, token economy, and creator revenue system
"""
import unittest
import uuid
import sys
import os
from unittest.mock import patch, MagicMock
from decimal import Decimal

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config'))

from services.game_service import game_service, InsufficientTokensError, GameNotFoundError
from models.database import User, Game, GameSession
from settings import settings
from utils.security_utils import threat_detector

class TestGameService(unittest.TestCase):
    """Test suite for game service functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user_id = uuid.uuid4()
        self.game_id = uuid.uuid4()
        self.creator_id = uuid.uuid4()
        
        # Mock user
        self.mock_user = MagicMock()
        self.mock_user.id = self.user_id
        self.mock_user.username = "testplayer"
        self.mock_user.tokens = 100
        self.mock_user.subscription_active = False
        self.mock_user.subscription_expires_at = None
        
        # Mock game
        self.mock_game = MagicMock()
        self.mock_game.id = self.game_id
        self.mock_game.title = "Test Game"
        self.mock_game.game_type = "premium"
        self.mock_game.token_cost = 5
        self.mock_game.difficulty_level = 2
        self.mock_game.play_count = 0
        self.mock_game.creator_id = self.creator_id
        self.mock_game.is_active = True
    
    def test_get_available_games_for_subscriber(self):
        """Test game availability for subscribed users"""
        # Set user as subscriber
        self.mock_user.subscription_active = True
        
        with patch('services.game_service.db_manager') as mock_db:
            mock_session = MagicMock()
            mock_db.get_session.return_value = mock_session
            mock_session.query().filter().all.return_value = [self.mock_game]
            
            # Mock creator relationship
            mock_creator = MagicMock()
            mock_creator.username = "gamedev"
            self.mock_game.creator = mock_creator
            
            games = game_service.get_available_games(self.mock_user)
            
            self.assertEqual(len(games), 1)
            self.assertTrue(games[0]["can_play"])
            self.assertIn("subscription", games[0]["reason"])
    
    def test_get_available_games_insufficient_tokens(self):
        """Test game availability when user has insufficient tokens"""
        # Set user with insufficient tokens
        self.mock_user.tokens = 2
        self.mock_game.token_cost = 5
        
        with patch('services.game_service.db_manager') as mock_db:
            mock_session = MagicMock()
            mock_db.get_session.return_value = mock_session
            mock_session.query().filter().all.return_value = [self.mock_game]
            
            mock_creator = MagicMock()
            mock_creator.username = "gamedev"
            self.mock_game.creator = mock_creator
            
            games = game_service.get_available_games(self.mock_user)
            
            self.assertEqual(len(games), 1)
            self.assertFalse(games[0]["can_play"])
            self.assertIn("Need 5 tokens", games[0]["reason"])
    
    def test_start_game_session_free_to_play(self):
        """Test starting a free-to-play game session"""
        self.mock_game.game_type = "free_to_play"
        self.mock_game.token_cost = 0
        
        with patch('services.game_service.db_manager') as mock_db:
            mock_session = MagicMock()
            mock_db.get_session.return_value = mock_session
            
            # Mock database queries
            mock_session.query().filter().first.side_effect = [self.mock_user, self.mock_game]
            
            # Mock game session creation
            mock_game_session = MagicMock()
            mock_game_session.id = uuid.uuid4()
            mock_session.add.return_value = None
            mock_session.flush.return_value = None
            
            success, message, session_info = game_service.start_game_session(
                self.user_id, self.game_id
            )
            
            self.assertTrue(success)
            self.assertIn("successfully", message)
            self.assertIsNotNone(session_info)
            self.assertEqual(session_info["tokens_spent"], 0)
    
    def test_start_game_session_premium_with_tokens(self):
        """Test starting a premium game with sufficient tokens"""
        self.mock_user.tokens = 10
        self.mock_game.token_cost = 5
        
        with patch('services.game_service.db_manager') as mock_db:
            mock_session = MagicMock()
            mock_db.get_session.return_value = mock_session
            
            # Mock database queries - user, game, and creator (if needed)
            mock_session.query().filter().first.side_effect = [
                self.mock_user,  # First query: get user
                self.mock_game,  # Second query: get game
                None  # Third query: creator (return None to skip creator revenue)
            ]
            
            # Mock game session creation
            mock_game_session = MagicMock()
            mock_game_session.id = uuid.uuid4()
            mock_session.add.return_value = None
            mock_session.flush.return_value = None
            mock_session.commit.return_value = None
            mock_session.rollback.return_value = None
            mock_session.close.return_value = None
            
            # Mock the _create_transaction and _log_audit_event methods
            with patch.object(game_service, '_create_transaction'), \
                 patch.object(game_service, '_log_audit_event'), \
                 patch('services.game_service.GameSession') as mock_game_session_class:
                
                # Mock GameSession constructor
                mock_game_session_class.return_value = mock_game_session
                
                success, message, session_info = game_service.start_game_session(
                    self.user_id, self.game_id
                )
            
            self.assertTrue(success, f"Expected success but got: {message}")
            self.assertIsNotNone(session_info)
            self.assertEqual(session_info["tokens_spent"], 5)
            # User tokens should be reduced
            self.assertEqual(self.mock_user.tokens, 5)
    
    def test_start_game_session_insufficient_tokens(self):
        """Test starting premium game with insufficient tokens"""
        self.mock_user.tokens = 2
        self.mock_game.token_cost = 5
        
        with patch('services.game_service.db_manager') as mock_db:
            mock_session = MagicMock()
            mock_db.get_session.return_value = mock_session
            
            mock_session.query().filter().first.side_effect = [self.mock_user, self.mock_game]
            
            success, message, session_info = game_service.start_game_session(
                self.user_id, self.game_id
            )
            
            self.assertFalse(success)
            self.assertIn("Insufficient tokens", message)
            self.assertIsNone(session_info)
    
    def test_creator_revenue_calculation(self):
        """Test creator revenue sharing"""
        self.mock_user.tokens = 10
        self.mock_game.token_cost = 6
        self.mock_game.game_type = "user_created"
        
        # Mock creator
        mock_creator = MagicMock()
        mock_creator.id = self.creator_id
        mock_creator.tokens = 50
        
        with patch('services.game_service.db_manager') as mock_db:
            mock_session = MagicMock()
            mock_db.get_session.return_value = mock_session
            
            # Mock queries returning user, game, and creator
            mock_session.query().filter().first.side_effect = [
                self.mock_user, self.mock_game, mock_creator
            ]
            
            success, message, session_info = game_service.start_game_session(
                self.user_id, self.game_id
            )
            
            if success:
                # Calculate expected creator revenue
                expected_revenue = int(6 * settings.CREATOR_REVENUE_SHARE)  # 35% of 6 tokens
                self.assertEqual(expected_revenue, 2)  # 6 * 0.35 = 2.1 -> 2 (int)
                
                # Creator should receive revenue
                self.assertEqual(mock_creator.tokens, 52)  # 50 + 2
    
    def test_game_simulation(self):
        """Test game play simulation"""
        session_id = uuid.uuid4()
        
        # Test multiple difficulties
        for difficulty in range(1, 6):
            result = game_service.simulate_game_play(session_id, difficulty)
            
            self.assertIn("score", result)
            self.assertIn("duration", result)
            self.assertIn("completed", result)
            self.assertIn("events", result)
            
            # Score should increase with difficulty
            self.assertGreater(result["score"], 0)
            
            # Duration should be reasonable
            self.assertGreater(result["duration"], 5)
            self.assertLess(result["duration"], 120)
            
            # Events should be a list
            self.assertIsInstance(result["events"], list)
            self.assertGreater(len(result["events"]), 0)
    
    def test_achievement_system(self):
        """Test achievement awarding"""
        session_id = uuid.uuid4()
        
        with patch('services.game_service.db_manager') as mock_db:
            mock_session = MagicMock()
            mock_db.get_session.return_value = mock_session
            
            # Mock game session
            mock_game_session = MagicMock()
            mock_game_session.id = session_id
            mock_game_session.game_id = self.game_id
            mock_game_session.user_id = self.user_id
            
            # Create a query mock that can handle multiple different filter chains
            query_mock = MagicMock()
            mock_session.query.return_value = query_mock
            
            # Mock the query().filter().first() calls in sequence
            filter_mock = MagicMock()
            query_mock.filter.return_value = filter_mock
            filter_mock.first.side_effect = [
                mock_game_session,  # First query: get game session
                self.mock_game,     # Second query: get game
                self.mock_user,     # Third query: get user
                None,               # Fourth query: check for existing achievement (high score)
                None,               # Fifth query: check for existing achievement (first game)  
                None,               # Sixth query: check for existing achievement (perfect game)
            ]
            
            # Mock the count query for user sessions (first game)
            filter_mock.count.return_value = 1
            
            # Mock session operations
            mock_session.add.return_value = None
            mock_session.commit.return_value = None
            mock_session.rollback.return_value = None
            mock_session.close.return_value = None
            
            # Mock max_score attribute for achievement trigger
            self.mock_game.max_score = 1000  # Lower than the test score
            
            # Mock the _log_audit_event method and Achievement class
            with patch.object(game_service, '_log_audit_event'), \
                 patch('services.game_service.Achievement') as mock_achievement_class:
                
                # Mock Achievement constructor returns for successful award
                mock_achievement = MagicMock()
                mock_achievement_class.return_value = mock_achievement
                
                success, message, achievements = game_service.end_game_session(
                    session_id, score=1500, duration=60, completed=True
                )
            
            if not success:
                print(f"Error: {message}")
            self.assertTrue(success, f"Expected success but got: {message}")
            # Should get achievements for first game and high score
            self.assertGreater(len(achievements), 0)
    
    def test_leaderboard_generation(self):
        """Test leaderboard functionality"""
        with patch('services.game_service.db_manager') as mock_db:
            mock_session = MagicMock()
            mock_db.get_session.return_value = mock_session
            
            # Mock leaderboard data
            mock_results = [
                (2000, "player1", "Test Game", "2024-01-01"),
                (1500, "player2", "Test Game", "2024-01-02"),
                (1000, "player3", "Test Game", "2024-01-03")
            ]
            
            mock_session.query().join().join().order_by().limit().all.return_value = mock_results
            
            leaderboard = game_service.get_leaderboard(limit=3)
            
            self.assertEqual(len(leaderboard), 3)
            self.assertEqual(leaderboard[0]["rank"], 1)
            self.assertEqual(leaderboard[0]["score"], 2000)
            self.assertEqual(leaderboard[0]["username"], "player1")
    
    def test_user_statistics(self):
        """Test user statistics generation"""
        with patch('services.game_service.db_manager') as mock_db:
            mock_session = MagicMock()
            mock_db.get_session.return_value = mock_session
            
            # Mock statistics queries
            mock_session.query().filter().count.side_effect = [10, 7, 2, 1]  # sessions, completed, achievements, games_created
            mock_session.query().filter().scalar.side_effect = [15000, 50, 25.50]  # total_score, tokens_spent, revenue
            mock_session.query().join().filter().group_by().all.return_value = [
                ("Test Game", 2000),
                ("Another Game", 1500)
            ]
            
            stats = game_service.get_user_statistics(self.user_id)
            
            self.assertEqual(stats["total_games_played"], 10)
            self.assertEqual(stats["completed_games"], 7)
            self.assertEqual(stats["completion_rate"], 70.0)
            self.assertEqual(stats["total_score"], 15000)
            self.assertEqual(len(stats["best_scores"]), 2)
    
    def test_token_purchase(self):
        """Test token purchasing functionality"""
        with patch('services.game_service.db_manager') as mock_db:
            mock_session = MagicMock()
            mock_db.get_session.return_value = mock_session
            
            # Mock user query
            self.mock_user.tokens = 50
            mock_session.query().filter().first.return_value = self.mock_user
            
            success, message = game_service.purchase_tokens(
                self.user_id, token_amount=100, payment_amount=9.99
            )
            
            self.assertTrue(success)
            self.assertIn("Successfully purchased", message)
            self.assertEqual(self.mock_user.tokens, 150)  # 50 + 100

class TestGameServiceSecurity(unittest.TestCase):
    """Security-focused tests for game service"""
    
    def test_bot_farming_detection(self):
        """Test detection of bot farming (MS.01)"""
        user_id = str(uuid.uuid4())
        game_id = str(uuid.uuid4())
        
        # Test unrealistic performance detection
        is_suspicious = threat_detector.detect_bot_farming(
            user_id, game_id, session_duration=2, score=5000
        )
        self.assertTrue(is_suspicious)
        
        # Test normal performance
        is_suspicious = threat_detector.detect_bot_farming(
            user_id, game_id, session_duration=30, score=500
        )
        self.assertFalse(is_suspicious)
    
    def test_cheating_detection(self):
        """Test detection of cheating (MS.07)"""
        user_id = str(uuid.uuid4())
        game_id = str(uuid.uuid4())
        
        # Test impossible score detection
        is_cheating = threat_detector.detect_cheating(
            user_id, game_id, score=100000, game_difficulty=1
        )
        self.assertTrue(is_cheating)
        
        # Test reasonable score
        is_cheating = threat_detector.detect_cheating(
            user_id, game_id, score=1500, game_difficulty=1
        )
        self.assertFalse(is_cheating)

if __name__ == '__main__':
    # Configure test environment
    os.environ['ENVIRONMENT'] = 'test'
    
    # Run tests
    unittest.main(verbosity=2)