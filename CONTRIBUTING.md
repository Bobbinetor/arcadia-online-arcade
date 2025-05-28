# Contributing to Arcadia Online Arcade Platform

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Docker and Docker Compose
- Git

### Setup Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/arcadia-online-arcade.git
   cd arcadia-online-arcade
   ```

2. **Make setup script executable and run it:**
   ```bash
   chmod +x run.sh
   ./run.sh --setup-only
   ```

3. **Start the application:**
   ```bash
   ./run.sh
   ```

### Development Commands

- **Quick start (skip tests):** `./run.sh --quick`
- **Run tests only:** `./run.sh --test-only`
- **Run without database:** `./run.sh --no-db`
- **Development mode:** `./run.sh --dev`

### Code Quality

Before submitting a PR, ensure:

```bash
# Run tests
pytest tests/ -v --cov=src

# Security scan
bandit -r src/

# Code formatting
black src/ tests/
flake8 src/ tests/
```

## 🏗️ Architecture

- **Backend**: Python with SQLAlchemy ORM
- **Database**: PostgreSQL with Redis for caching
- **Authentication**: JWT tokens with bcrypt password hashing
- **Security**: STRIDE threat modeling, input validation, audit logging
- **UI**: Rich terminal interface with colorama

## 🔒 Security Guidelines

1. Always validate user inputs
2. Use parameterized queries for database operations
3. Implement proper error handling without information leakage
4. Follow the principle of least privilege
5. Log security events for audit trails

## 📝 Commit Guidelines

- Use conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `security:`
- Write clear, descriptive commit messages
- Keep commits atomic and focused

## 🐛 Bug Reports

When reporting bugs, include:
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version)
- Relevant log output

## 💡 Feature Requests

For new features:
- Describe the use case
- Consider security implications
- Align with the project's arcade theme
- Think about the user personas (Marco, Alessia, Luca, Silvia)
