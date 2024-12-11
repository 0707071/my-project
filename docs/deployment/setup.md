# System Setup

## Overview

Setting up Karhuno for production requires careful planning because:
- System components are interdependent
- Security must be properly configured
- Performance needs optimization
- Monitoring must be comprehensive

## Prerequisites

### 1. System Requirements
Hardware and software needs:

```python
production_requirements = {
    'hardware': {
        'application_server': {
            'cpu': '4+ cores',
            'memory': '16+ GB RAM',
            'storage': '100+ GB SSD',
            'network': '100+ Mbps'
        },
        'database_server': {
            'cpu': '4+ cores',
            'memory': '32+ GB RAM',
            'storage': '500+ GB SSD',
            'network': '100+ Mbps'
        },
        'worker_nodes': {
            'cpu': '2+ cores per worker',
            'memory': '8+ GB RAM per worker',
            'storage': '50+ GB SSD per worker'
        }
    },
    'software': {
        'os': 'Ubuntu 20.04 LTS or newer',
        'python': '3.11',  # Strict requirement
        'postgresql': '13+',
        'redis': '6+',
        'nginx': 'Latest stable'
    }
}
```

### 2. Network Requirements
Configure network access:

```python
network_setup = {
    'firewall_rules': {
        'inbound': [
            '80/443 (HTTP/HTTPS)',
            '5432 (PostgreSQL)',
            '6379 (Redis)',
            '8000 (Gunicorn)'
        ],
        'outbound': [
            '443 (HTTPS for APIs)',
            '53 (DNS)',
            '123 (NTP)'
        ]
    },
    'security_groups': {
        'web_tier': ['80', '443'],
        'app_tier': ['8000'],
        'db_tier': ['5432', '6379']
    }
}
```

## Installation Process

### 1. Base System Setup
Prepare the system:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Add deadsnakes PPA for Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# Install system dependencies
sudo apt install -y python3.11 python3.11-venv python3.11-dev \
    postgresql-13 redis-server nginx supervisor \
    build-essential libpq-dev

# Create application user
sudo useradd -m -s /bin/bash karhuno
sudo usermod -aG sudo karhuno

# Create application directory
sudo mkdir -p /opt/karhuno
sudo chown karhuno:karhuno /opt/karhuno

# Create log directory
sudo mkdir -p /var/log/karhuno
sudo chown karhuno:karhuno /var/log/karhuno
```

### 2. Application Setup
Install application:

```bash
# Switch to application user
sudo su - karhuno

# Clone repository
git clone https://github.com/PavelBelove/karhuno.git /opt/karhuno
cd /opt/karhuno

# Create virtual environment with Python 3.11
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip and install wheel
pip install --upgrade pip wheel setuptools

# Install frozen dependencies
pip install -r requirements.frozen.txt

# Install production server packages
pip install gunicorn supervisor
```

### 3. Database Setup
Configure PostgreSQL:

```bash
# Create database and user
sudo -u postgres psql -c "CREATE DATABASE karhuno;"
sudo -u postgres psql -c "CREATE USER karhuno WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE karhuno TO karhuno;"

# Run migrations
flask db upgrade
```

### 4. Service Configuration
Configure services:

```bash
# Configure Redis
sudo cp /opt/karhuno/config/redis.conf /etc/redis/redis.conf
sudo systemctl restart redis

# Configure Nginx
sudo cp /opt/karhuno/config/nginx.conf /etc/nginx/sites-available/karhuno
sudo ln -s /etc/nginx/sites-available/karhuno /etc/nginx/sites-enabled/
sudo systemctl restart nginx

# Configure Supervisor
sudo cp /opt/karhuno/config/supervisor.conf /etc/supervisor/conf.d/karhuno.conf
sudo supervisorctl reread
sudo supervisorctl update
```

## Post-Installation

### 1. Security Setup
Configure security:

```bash
# Generate secret key
python -c "import secrets; print(secrets.token_hex(32))" > /opt/karhuno/.env

# Set up SSL certificates
sudo certbot --nginx -d your-domain.com

# Configure firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Monitoring Setup
Configure monitoring:

```bash
# Set up logging
sudo mkdir -p /var/log/karhuno
sudo chown karhuno:karhuno /var/log/karhuno

# Configure log rotation
sudo cp /opt/karhuno/config/logrotate.conf /etc/logrotate.d/karhuno
```

## Related Topics
- [Configuration Guide](configuration.md)
- [Security Setup](security.md)
- [Monitoring Setup](monitoring.md)
- [Development Setup](../developer/getting-started.md)