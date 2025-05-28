# 🎮 Arcadia Online Arcade Platform

A nostalgic online arcade platform that combines the spirit of 80s arcade halls with modern social and digital economy features.

## 🚀 Features

- **Secure Authentication**: Multi-factor authentication with JWT tokens
- **Token Economy**: Purchase tokens for premium games or subscription access
- **Creator Hub**: Users can create and publish their own arcade games
- **Social Features**: Chat, tournaments, and community interactions
- **Achievements**: Badge system and customizable arcade trophy case
- **Security-First**: Built with STRIDE threat modeling and secure-by-design principles

## 🏗️ Architecture

This is the terminal-based first release focusing on:
- Secure user authentication and session management
- Token-based game economy
- Basic game library with classic arcade titles
- Creator tools for game publishing
- Comprehensive audit logging

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.8+
- Docker and Docker Compose
- Git

### Installation

1. **Clone and setup the project:**
   ```bash
   git clone <repository-url>
   cd arcadia
   chmod +x setup_arcadia.sh
   ./setup_arcadia.sh
   ```

2. **Start the database:**
   ```bash
   docker-compose up -d
   ```

3. **Create virtual environment and install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python src/main.py
   ```

### Development Setup

1. **Install development dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run tests:**
   ```bash
   pytest tests/ -v --cov=src
   ```

3. **Security scanning:**
   ```bash
   bandit -r src/
   ```

4. **Code formatting:**
   ```bash
   black src/ tests/
   flake8 src/ tests/
   ```

## 🎯 User Personas

- **Marco "Il Competitivo"**: Competitive player focused on leaderboards and tournaments
- **Alessia "La Casual"**: Casual player enjoying subscription-based access
- **Luca "Il Creatore"**: Game creator monetizing through the platform
- **Silvia "La Social"**: Social gamer organizing gaming sessions

## 🔒 Security Features

- STRIDE threat analysis implementation
- Secure password hashing with bcrypt
- JWT-based authentication with expiration
- Input validation and rate limiting
- Comprehensive audit logging
- Static and dynamic security scanning

## 📊 Database Schema

Key entities:
- **Users**: Authentication, tokens, subscriptions
- **Games**: Game library with creator attribution
- **Game Sessions**: Play history and scoring
- **Transactions**: Token purchases and game spending
- **Achievements**: Badge and trophy system
- **Audit Logs**: Security and activity monitoring

## 🎮 Game Types

- **Premium Games**: Require tokens or subscription
- **Free-to-Play**: Basic access with optional token features
- **User-Created**: Community-generated content with revenue sharing

## 📈 Roadmap

### Sprint 1: Secure Foundation ✅
- Threat analysis and architecture
- Secure authentication system
- Basic game engine
- Audit logging

### Sprint 2: Core Gaming (Next)
- Game library implementation
- Token economy
- Creator Hub basics
- User profiles

### Sprint 3: Social Features
- Chat system with moderation
- Tournaments and leaderboards
- Achievement system

## 🤝 Contributing

1. Follow the secure coding guidelines
2. Write tests for new features
3. Run security scans before submitting
4. Update documentation

## 📝 License

This project is part of an academic security-focused software development exercise.
