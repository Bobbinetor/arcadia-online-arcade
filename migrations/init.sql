-- Arcadia Database Schema
-- Initial migration for terminal-based release

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    tokens INTEGER DEFAULT 100,
    subscription_active BOOLEAN DEFAULT FALSE,
    subscription_expires_at TIMESTAMP,
    profile_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Games table
CREATE TABLE games (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    creator_id UUID REFERENCES users(id) ON DELETE CASCADE,
    game_type VARCHAR(50) NOT NULL, -- 'premium', 'free_to_play', 'user_created'
    token_cost INTEGER DEFAULT 0,
    difficulty_level INTEGER DEFAULT 1 CHECK (difficulty_level BETWEEN 1 AND 5),
    max_score INTEGER DEFAULT 0,
    play_count INTEGER DEFAULT 0,
    revenue_generated DECIMAL(10,2) DEFAULT 0.00,
    game_data JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Game Sessions table
CREATE TABLE game_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    game_id UUID REFERENCES games(id) ON DELETE CASCADE,
    score INTEGER DEFAULT 0,
    tokens_spent INTEGER DEFAULT 0,
    duration_seconds INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT FALSE,
    session_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions table (for token purchases and game spending)
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL, -- 'token_purchase', 'game_play', 'creator_payout', 'subscription'
    amount DECIMAL(10,2) NOT NULL,
    tokens_involved INTEGER DEFAULT 0,
    description TEXT,
    reference_id UUID, -- Can reference game_id, session_id, etc.
    status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Achievements table
CREATE TABLE achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    achievement_type VARCHAR(100) NOT NULL,
    achievement_name VARCHAR(255) NOT NULL,
    description TEXT,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    achievement_data JSONB DEFAULT '{}'
);

-- Audit Log table (for security and monitoring)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    details JSONB DEFAULT '{}',
    severity VARCHAR(20) DEFAULT 'INFO',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_games_creator ON games(creator_id);
CREATE INDEX idx_games_type ON games(game_type);
CREATE INDEX idx_sessions_user ON game_sessions(user_id);
CREATE INDEX idx_sessions_game ON game_sessions(game_id);
CREATE INDEX idx_transactions_user ON transactions(user_id);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_timestamp ON audit_logs(created_at);

-- Insert some initial games
INSERT INTO games (title, description, game_type, token_cost, difficulty_level) VALUES
('Pixel Snake', 'Classic snake game with retro graphics', 'free_to_play', 0, 1),
('Space Invaders Classic', 'Defend Earth from alien invasion', 'premium', 2, 2),
('Tetris Challenge', 'Stack blocks and clear lines', 'premium', 3, 3),
('Pac-Man Adventure', 'Navigate mazes and collect dots', 'premium', 2, 2),
('Breakout Master', 'Break bricks with your paddle', 'free_to_play', 1, 1),
('Asteroids Shooter', 'Survive in the asteroid field', 'premium', 4, 4),
('Frogger Road Cross', 'Help the frog cross safely', 'free_to_play', 0, 2),
('Centipede Hunt', 'Shoot the descending centipede', 'premium', 3, 3);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_games_updated_at
    BEFORE UPDATE ON games
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Create a view for user statistics
CREATE VIEW user_stats AS
SELECT 
    u.id,
    u.username,
    u.tokens,
    u.subscription_active,
    COUNT(gs.id) as total_games_played,
    COALESCE(SUM(gs.score), 0) as total_score,
    COALESCE(SUM(gs.tokens_spent), 0) as total_tokens_spent,
    COUNT(g.id) as games_created
FROM users u
LEFT JOIN game_sessions gs ON u.id = gs.user_id
LEFT JOIN games g ON u.id = g.creator_id
GROUP BY u.id, u.username, u.tokens, u.subscription_active;

COMMENT ON DATABASE arcadia IS 'Arcadia Online Arcade Platform - Terminal Release v1.0';
