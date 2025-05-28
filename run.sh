#!/bin/bash

# Arcadia Platform - Easy Run Script
# This script handles the complete startup process for the Arcadia platform

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}$1${NC}"
}

# Print banner
print_banner() {
    echo -e "${CYAN}"
    cat << "EOF"
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                         🎮 ARCADIA PLATFORM 🎮                              ║
║                          Terminal Release v1.0                              ║
║                                                                              ║
║                  Easy startup script for development                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_header "🔍 Checking Prerequisites..."
    
    local missing_deps=()
    
    # Check Python
    if command_exists python3; then
        python_version=$(python3 --version 2>&1 | awk '{print $2}')
        print_success "Python $python_version found"
    else
        missing_deps+=("python3")
    fi
    
    # Check Docker
    if command_exists docker; then
        docker_version=$(docker --version | awk '{print $3}' | sed 's/,//')
        print_success "Docker $docker_version found"
    else
        missing_deps+=("docker")
    fi
    
    # Check Docker Compose
    if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
        print_success "Docker Compose found"
    else
        missing_deps+=("docker-compose")
    fi
    
    # Check pip
    if command_exists pip3 || python3 -m pip --version >/dev/null 2>&1; then
        print_success "pip found"
    else
        missing_deps+=("pip3")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        echo "Please install the missing dependencies and try again."
        echo ""
        echo "Installation guides:"
        echo "- Python 3.8+: https://www.python.org/downloads/"
        echo "- Docker: https://docs.docker.com/get-docker/"
        echo "- Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    print_success "All prerequisites satisfied"
}

# Setup virtual environment
setup_venv() {
    print_header "🐍 Setting up Python Virtual Environment..."
    
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    # Upgrade pip
    print_status "Upgrading pip..."
    python -m pip install --upgrade pip
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    
    print_success "Python environment ready"
}

# Start database
start_database() {
    print_header "🗄️  Starting Database Services..."
    
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml not found. Make sure you're in the project root."
        exit 1
    fi
    
    print_status "Starting PostgreSQL and Redis..."
    docker-compose up -d postgres redis
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    for i in {1..30}; do
        if docker-compose exec -T postgres pg_isready -U arcadia_user -d arcadia >/dev/null 2>&1; then
            print_success "Database is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Database failed to start within 30 seconds"
            print_status "Checking database logs..."
            docker-compose logs postgres
            exit 1
        fi
        echo -n "."
        sleep 1
    done
}

# Run tests
run_tests() {
    print_header "🧪 Running Tests..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    print_status "Running unit tests..."
    if python -m pytest tests/ -v --tb=short; then
        print_success "All tests passed"
    else
        print_warning "Some tests failed - check output above"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Run security scan
run_security_scan() {
    print_header "🔒 Running Security Scan..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    print_status "Running Bandit security scan..."
    if command_exists bandit; then
        bandit -r src/ -f txt || print_warning "Security issues found - review output above"
    else
        print_warning "Bandit not installed - skipping security scan"
    fi
}

# Start application
start_application() {
    print_header "🚀 Starting Arcadia Platform..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    print_status "Launching terminal interface..."
    python src/main.py
}

# Cleanup function
cleanup() {
    print_header "🧹 Cleanup..."
    print_status "Stopping services..."
    docker-compose down
    print_success "Cleanup complete"
}

# Show usage
show_usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --help, -h          Show this help message"
    echo "  --quick, -q         Quick start (skip tests and security scan)"
    echo "  --test-only         Run tests only"
    echo "  --setup-only        Setup environment only"
    echo "  --no-db             Skip database startup"
    echo "  --dev               Development mode with debug output"
    echo ""
    echo "Examples:"
    echo "  $0                  Full startup with all checks"
    echo "  $0 --quick          Quick startup for development"
    echo "  $0 --test-only      Run tests without starting the app"
}

# Parse command line arguments
QUICK_MODE=false
TEST_ONLY=false
SETUP_ONLY=false
NO_DB=false
DEV_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_usage
            exit 0
            ;;
        --quick|-q)
            QUICK_MODE=true
            shift
            ;;
        --test-only)
            TEST_ONLY=true
            shift
            ;;
        --setup-only)
            SETUP_ONLY=true
            shift
            ;;
        --no-db)
            NO_DB=true
            shift
            ;;
        --dev)
            DEV_MODE=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_banner
    
    # Set up trap for cleanup on exit
    trap cleanup EXIT INT TERM
    
    # Check prerequisites
    check_prerequisites
    
    # Setup Python environment
    setup_venv
    
    if [ "$SETUP_ONLY" = true ]; then
        print_success "Setup complete. Use './run_arcadia.sh' to start the application."
        exit 0
    fi
    
    # Start database unless disabled
    if [ "$NO_DB" = false ]; then
        start_database
    fi
    
    # Run tests unless in quick mode
    if [ "$QUICK_MODE" = false ] && [ "$TEST_ONLY" = false ]; then
        run_tests
    fi
    
    if [ "$TEST_ONLY" = true ]; then
        exit 0
    fi
    
    # Run security scan unless in quick mode
    if [ "$QUICK_MODE" = false ]; then
        run_security_scan
    fi
    
    # Start the application
    start_application
}

# Run main function
main "$@"