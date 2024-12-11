# Getting Started

## Environment Setup

### 1. Prerequisites
- Python 3.11 (strict requirement)
- PostgreSQL 13+
- Redis 6+
- Git

### 2. Installation
```bash
# Clone repository
git clone https://github.com/PavelBelove/karhuno.git
cd karhuno

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Upgrade pip and install wheel
pip install --upgrade pip wheel setuptools

# Install dependencies from frozen requirements
pip install -r requirements.frozen.txt
```

### 3. Database Setup
```bash
# Create database and user (as postgres superuser)
sudo -u postgres psql -c "CREATE USER flask WITH PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "CREATE DATABASE karhuno OWNER flask;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE karhuno TO flask;"
sudo -u postgres psql -d karhuno -c "GRANT ALL ON SCHEMA public TO flask;"

# If you need to reset the database:
sudo -u postgres psql -c "ALTER DATABASE karhuno OWNER TO postgres;"
sudo -u postgres psql -c "DROP USER IF EXISTS flask;"
sudo -u postgres psql -c "CREATE USER flask WITH PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "ALTER DATABASE karhuno OWNER TO flask;"
```

### 4. Configuration
```bash
# Copy example environment file
cp .env.example .env
```

Edit `.env` file with the following configuration:
```env
# Flask configuration
FLASK_APP=run.py
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your_generated_key

# Database configuration (use strong password without special characters)
DATABASE_URL=postgresql://flask:your_secure_password@localhost:5432/karhuno

# Redis configuration
REDIS_URL=redis://localhost:6379/0

# API Keys
XMLSTOCK_USER=your_xmlstock_user
XMLSTOCK_KEY=your_xmlstock_key
OPENAI_API_KEY=your_openai_key
```
### 5. Database Initialization
```bash
# Initialize database migrations
flask db init
flask db migrate -m "initial migration"
flask db upgrade

# Create admin user through Flask shell
flask shell
```

In Flask shell:
```python
from app.models.user import User, Role
from app import db

admin = User(
    username='admin',
    email='admin@example.com',
    is_admin=True,
    role=Role.ANALYST
)
admin.set_password('your_admin_password')
db.session.add(admin)
db.session.commit()
exit()
```

## Development Scripts

### Start Development Environment
```bash
# start.sh
#!/bin/bash

# Start Redis if not running
redis-server --daemonize yes

# Start Celery worker
celery -A app.celery worker --loglevel=info &
echo $! > celery.pid

# Start Flask development server
flask run --debug
```

### Stop Development Environment
```bash
# stop.sh
#!/bin/bash

# Kill Celery workers (sometimes requires force)
if [ -f celery.pid ]; then
    pid=$(cat celery.pid)
    kill -9 $pid
    rm celery.pid
fi

# Stop Redis
redis-cli shutdown

# Note: Flask server stops with Ctrl+C
```

Usage:
```bash
# Start development environment
./start.sh

# Stop development environment
./stop.sh
```

## Development Tools

### 1. Testing
```bash
# Install development tools
pip install -r requirements.dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

### 2. Code Quality
```bash
# Run linting
flake8 app tests

# Run type checking
mypy app
```

## Development Workflow

### 1. Code Style
- Follow PEP 8 guidelines
- Use type hints
- Write docstrings in Google format
- Keep functions focused and under 50 lines

### 2. Git Workflow
```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes and commit
git add .
git commit -m "feat: description"

# Push changes
git push origin feature/your-feature
```

### 3. Testing
```bash
# Run specific test file
pytest tests/test_search_tasks.py

# Run with verbose output
pytest -v

# Run tests matching pattern
pytest -k "test_search"
```

## Related Topics
- [Development Guide](development.md)
- [API Documentation](../api/overview.md)
- [Testing Guide](testing.md)
- [Deployment Guide](../deployment/setup.md)

### Windows Development Scripts

Create these files in the project root:

```batch:start.bat
@echo off
echo Starting development environment...

:: Start Redis
echo Starting Redis...
start /B redis-server

:: Start Celery worker
echo Starting Celery...
start /B celery -A app.celery worker --loglevel=info --pool=solo

:: Start Flask development server
echo Starting Flask...
start /B flask run --debug

echo All services started! Press any key to stop all services...
pause

:: Cleanup
taskkill /F /IM redis-server.exe
taskkill /F /IM celery.exe
taskkill /F /IM python.exe
```

```batch:stop.bat
@echo off
echo Stopping all services...

:: Stop all services
taskkill /F /IM redis-server.exe
taskkill /F /IM celery.exe
taskkill /F /IM python.exe

echo All services stopped!
pause
```

Usage:
1. Double-click `start.bat` to start all services
2. Press any key in the console window to stop all services
3. Alternatively, use `stop.bat` to force-stop all services

Note: Make sure Redis is installed and added to system PATH. You can download Redis for Windows from [GitHub](https://github.com/microsoftarchive/redis/releases).