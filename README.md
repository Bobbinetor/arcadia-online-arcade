# 🎮 Arcadia Online Arcade Platform

A secure, terminal-based online arcade platform that combines the nostalgia of 80s arcade halls with modern security practices, digital economy features, and community-driven game creation.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/database-PostgreSQL-336791.svg)](https://www.postgresql.org/)
[![Security](https://img.shields.io/badge/security-STRIDE%20analyzed-green.svg)](docs/security/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 Features

### 🔐 Security-First Design
- **JWT Authentication**: Secure token-based authentication with configurable expiration
- **Password Security**: bcrypt hashing with salt for password storage
- **Rate Limiting**: Protection against brute force attacks and abuse
- **Audit Logging**: Comprehensive security event tracking and monitoring
- **Input Validation**: Strict validation for all user inputs
- **STRIDE Analysis**: Threat modeling and security-by-design implementation

### 🪙 Digital Economy
- **Token System**: Virtual currency for premium game access
- **Creator Revenue**: 35% revenue sharing for game creators
- **Subscription Model**: Premium subscription for unlimited access
- **Transaction Tracking**: Complete financial audit trail
- **Flexible Pricing**: Configurable token costs per game

### 🎮 Gaming Platform
- **Classic Arcade Games**: Built-in library of retro favorites
- **User-Created Content**: Community game creation and publishing
- **Achievement System**: Badge collection and progress tracking
- **Leaderboards**: Global and per-game scoring systems
- **Game Analytics**: Play count, completion rates, and user statistics

### 👥 Community Features
- **User Profiles**: Customizable player profiles with statistics
- **Creator Tools**: Game publishing and revenue management
- **Social Stats**: Friend connections and gaming sessions
- **Content Moderation**: Safety features and community guidelines

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Terminal CLI  │    │  Authentication │    │   Game Engine   │
│                 │◄──►│    Service      │◄──►│                 │
│  - Menu System  │    │  - JWT Tokens   │    │  - Session Mgmt │
│  - User Input   │    │  - Rate Limiting│    │  - Score Track  │
│  - Game Display │    │  - Audit Logs   │    │  - Achievements │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │   Database      │
                    │                 │
                    │  - Users        │
                    │  - Games        │
                    │  - Sessions     │
                    │  - Transactions │
                    │  - Achievements │
                    │  - Audit Logs   │
                    └─────────────────┘
```

## 🛠️ Quick Start

### Prerequisites
- **Python 3.8+** with pip
- **Docker & Docker Compose** for database
- **Git** for version control

### 🚀 Easy Setup (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/arcadia-online-arcade.git
cd arcadia-online-arcade

# 2. Make the run script executable
chmod +x run.sh

# 3. Start the complete platform (includes database setup)
./run.sh
```

### 📋 Manual Setup (Advanced)

<details>
<summary>Click to expand manual setup instructions</summary>

```bash
# 1. Start PostgreSQL and Redis
docker-compose up -d

# 2. Create virtual environment
python -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment (optional)
cp .env.example .env
# Edit .env with your preferred settings

# 5. Run the application
python src/main.py
```

</details>

### 🎮 Using the Platform

1. **Register a new account** or use demo credentials:
   - Email: `demo@arcadia.local`
   - Password: `Demo123!`

2. **Browse available games** in the game library

3. **Play games** using your token balance or subscription

4. **Track achievements** and climb the leaderboards

5. **Create games** (future feature) and earn revenue

## 📊 Database Schema

### Core Entities

#### Users Table
```sql
users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    username VARCHAR(50) UNIQUE,
    password_hash VARCHAR(255),
    tokens INTEGER DEFAULT 100,
    subscription_active BOOLEAN DEFAULT FALSE,
    subscription_expires_at TIMESTAMP,
    profile_data JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
)
```

#### Games Table
```sql
games (
    id UUID PRIMARY KEY,
    title VARCHAR(255),
    description TEXT,
    creator_id UUID REFERENCES users(id),
    game_type VARCHAR(50), -- 'premium', 'free_to_play', 'user_created'
    token_cost INTEGER DEFAULT 0,
    difficulty_level INTEGER DEFAULT 1,
    max_score INTEGER DEFAULT 0,
    play_count INTEGER DEFAULT 0,
    revenue_generated DECIMAL(10,2),
    game_data JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

#### Game Sessions Table
```sql
game_sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    game_id UUID REFERENCES games(id),
    score INTEGER DEFAULT 0,
    tokens_spent INTEGER DEFAULT 0,
    duration_seconds INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT FALSE,
    session_data JSONB,
    created_at TIMESTAMP
)
```

<details>
<summary>View additional tables (Transactions, Achievements, Audit Logs)</summary>

#### Transactions Table
```sql
transactions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    transaction_type VARCHAR(50), -- 'token_purchase', 'game_play', 'creator_payout'
    amount DECIMAL(10,2),
    tokens_involved INTEGER DEFAULT 0,
    description TEXT,
    reference_id UUID,
    status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP
)
```

#### Achievements Table
```sql
achievements (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    achievement_type VARCHAR(100),
    achievement_name VARCHAR(255),
    description TEXT,
    earned_at TIMESTAMP,
    achievement_data JSONB
)
```

#### Audit Logs Table
```sql
audit_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    action VARCHAR(100),
    resource_type VARCHAR(50),
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    details JSONB,
    severity VARCHAR(20) DEFAULT 'INFO',
    created_at TIMESTAMP
)
```

</details>

## 🎮 Game Library

### Built-in Games

| Game | Type | Cost | Difficulty | Description |
|------|------|------|------------|-------------|
| **Pixel Snake** | Free-to-Play | 0 tokens | ⭐ | Classic snake game with retro graphics |
| **Space Invaders Classic** | Premium | 2 tokens | ⭐⭐ | Defend Earth from alien invasion |
| **Tetris Challenge** | Premium | 3 tokens | ⭐⭐⭐ | Stack blocks and clear lines |
| **Pac-Man Adventure** | Premium | 2 tokens | ⭐⭐ | Navigate mazes and collect dots |
| **Breakout Master** | Free-to-Play | 1 token | ⭐ | Break bricks with your paddle |
| **Asteroids Shooter** | Premium | 4 tokens | ⭐⭐⭐⭐ | Survive in the asteroid field |
| **Frogger Road Cross** | Free-to-Play | 0 tokens | ⭐⭐ | Help the frog cross safely |
| **Centipede Hunt** | Premium | 3 tokens | ⭐⭐⭐ | Shoot the descending centipede |

### Game Types

- **🆓 Free-to-Play**: No cost or minimal tokens required
- **💎 Premium**: Requires tokens or active subscription
- **👥 User-Created**: Community-generated content with revenue sharing

## 💰 Economy System

### Token Economics
- **Starting Balance**: 100 tokens for new users
- **Token Value**: Approximately $0.01 per token
- **Purchase Options**: Various token packages available
- **Earning Tokens**: Create popular games and earn revenue

### Creator Revenue Sharing
- **Revenue Split**: 35% to creators, 65% to platform
- **Payout System**: Automatic token distribution
- **Creator Tools**: Analytics and revenue tracking
- **Quality Control**: Community moderation and rating system

### Subscription Benefits
- **Premium Access**: Unlimited play of premium games
- **Exclusive Content**: Early access to new releases
- **Creator Tools**: Advanced game creation features
- **No Ads**: Clean gaming experience

## 🔒 Security Implementation

### STRIDE Threat Model Coverage

| Threat | Mitigation | Implementation |
|--------|------------|----------------|
| **Spoofing** | Strong Authentication | JWT tokens, password hashing |
| **Tampering** | Data Integrity | Database constraints, audit logs |
| **Repudiation** | Audit Logging | Comprehensive event tracking |
| **Information Disclosure** | Access Control | Role-based permissions |
| **Denial of Service** | Rate Limiting | Request throttling, resource limits |
| **Elevation of Privilege** | Principle of Least Privilege | Minimal required permissions |

### Security Features
- **Password Policy**: Minimum 8 characters, complexity requirements
- **Session Management**: Secure JWT with configurable expiration
- **Rate Limiting**: 5 failed attempts = 5-minute lockout
- **Input Validation**: Strict validation for all user inputs
- **Audit Trail**: All actions logged with timestamps and user context
- **Error Handling**: Secure error messages without information leakage

## 🧪 Testing

### Running Tests

```bash
# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run specific test files
pytest tests/test_authentication.py -v
pytest tests/test_game_service.py -v

# Run security-focused tests
pytest tests/ -k "security" -v
```

### Test Coverage

The test suite covers:
- ✅ **Authentication Service**: Registration, login, JWT validation
- ✅ **Game Service**: Game sessions, token economy, achievements
- ✅ **Database Models**: Data integrity and relationships
- ✅ **Security Features**: Rate limiting, input validation, audit logging
- ✅ **Integration Tests**: End-to-end user workflows

### Security Testing

```bash
# Static security analysis
bandit -r src/ -f json -o security-report.json

# Code quality checks
flake8 src/ tests/ --max-line-length=100
black src/ tests/ --check
mypy src/
```

## 📈 Development Roadmap

### ✅ Phase 1: Foundation (Current)
- [x] Secure authentication system
- [x] Database schema and models
- [x] Basic game service implementation
- [x] Token economy foundation
- [x] Achievement system
- [x] Comprehensive testing suite
- [x] Security audit and STRIDE analysis

### 🚧 Phase 2: Enhanced Gaming (In Progress)
- [ ] Interactive game implementations
- [ ] Real-time game simulation
- [ ] Advanced achievement system
- [ ] User profile enhancements
- [ ] Game creation tools (basic)

### 🔮 Phase 3: Community Features (Planned)
- [ ] Social features and friend system
- [ ] Tournament system
- [ ] Chat and messaging
- [ ] Content moderation tools
- [ ] Mobile companion app

### 🌟 Phase 4: Platform Expansion (Future)
- [ ] Web interface
- [ ] Advanced creator tools
- [ ] Marketplace for game assets
- [ ] Streaming and spectator modes
- [ ] AI-powered game recommendations

## 🛠️ Development

### Project Structure

```
arcadia/
├── src/                    # Main application code
│   ├── main.py            # Application entry point
│   ├── cli/               # Terminal interface
│   ├── models/            # Database models
│   ├── services/          # Business logic services
│   ├── utils/             # Utility functions
│   └── games/             # Game implementations
├── tests/                 # Test suite
├── config/                # Configuration files
├── migrations/            # Database migrations
├── docker-compose.yml     # Database services
├── requirements.txt       # Python dependencies
├── run.sh                # Easy setup script
└── docs/                 # Documentation
```

### Development Commands

```bash
# Quick development start
./run.sh --dev

# Setup only (no start)
./run.sh --setup-only

# Run without database
./run.sh --no-db

# Test only
./run.sh --test-only

# Quick start (skip tests)
./run.sh --quick
```

### Contributing Guidelines

1. **Fork and Clone**: Create your own fork of the repository
2. **Branch**: Create a feature branch from `main`
3. **Code**: Follow the existing code style and patterns
4. **Test**: Add tests for new features and ensure all tests pass
5. **Security**: Run security scans before submitting
6. **Document**: Update documentation for new features
7. **Pull Request**: Submit a PR with clear description

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 🎯 User Stories & Personas

### Primary User Personas

#### 🏆 Marco "Il Competitivo" (Competitive Gamer)
- **Goals**: Achieve high scores, compete on leaderboards
- **Features**: Advanced statistics, achievement tracking, tournament modes
- **Usage**: Daily active player, willing to purchase tokens for premium games

#### 🎮 Alessia "La Casual" (Casual Player)
- **Goals**: Relaxing gaming experience, variety of games
- **Features**: Subscription model, easy game discovery, social features
- **Usage**: Weekly sessions, prefers unlimited access over pay-per-play

#### 👨‍💻 Luca "Il Creatore" (Game Creator)
- **Goals**: Create and monetize games, build community
- **Features**: Game creation tools, revenue analytics, community feedback
- **Usage**: Creates 2-3 games per month, active in creator community

#### 👥 Silvia "La Social" (Social Gamer)
- **Goals**: Play with friends, organize gaming sessions
- **Features**: Friend systems, multiplayer modes, chat features
- **Usage**: Organizes weekly gaming nights, shares achievements

## 📱 Platform Support

### Current Support
- ✅ **Terminal/CLI**: Full-featured terminal interface
- ✅ **Linux**: Native support
- ✅ **macOS**: Native support
- ✅ **Windows**: WSL recommended

### Future Support
- 🔮 **Web Browser**: React-based web interface
- 🔮 **Mobile Apps**: iOS and Android companion apps
- 🔮 **Desktop GUI**: Electron-based desktop application

## 🤝 Community

### Getting Help
- **Documentation**: Check this README and inline code documentation
- **Issues**: Create GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas

### Contributing
- **Code**: Submit pull requests for features and bug fixes
- **Documentation**: Help improve documentation and examples
- **Testing**: Report bugs and help with testing new features
- **Games**: Create and share new games for the platform

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Security Design**: Based on STRIDE threat modeling methodology
- **Game Inspiration**: Classic arcade games from the 1980s
- **Community**: Built for gamers, by gamers
- **Academic Context**: Security-focused software development exercise


---

<div align="center">

**Built with ❤️ for the gaming community**

[⭐ Star this repo](https://github.com/bobbinetor/arcadia-online-arcade) | [🍴 Fork it](https://github.com/bobbinetor/arcadia-online-arcade/fork) | [📖 Read the docs](docs/)

</div>
