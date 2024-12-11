# Configuration Guide

## Overview

Proper configuration is critical because:
- Multiple components need coordination
- Security settings must be precise
- Performance depends on correct settings
- Different environments need different configs

## Configuration Files

### 1. Environment Variables
Core system configuration:

```bash
# Production environment file (.env)
# Basic Configuration
FLASK_ENV=production
FLASK_APP=run.py
SECRET_KEY=your-generated-key

# Database Configuration
DATABASE_URL=postgresql://karhuno:password@localhost:5432/karhuno
REDIS_URL=redis://localhost:6379/0

# API Keys
XMLSTOCK_API_KEY=your_api_key
OPENAI_API_KEY=your_api_key

# Worker Configuration
CELERY_WORKERS=4
GUNICORN_WORKERS=4

# Resource Limits
MAX_CONTENT_LENGTH=10485760  # 10MB
RATELIMIT_DEFAULT=300/hour
RATELIMIT_STORAGE_URL=redis://localhost:6379/1
```

### 2. Application Configuration
Flask application settings:

```python
class ProductionConfig:
    """
    Production configuration settings.
    
    Why these values:
    - Security first
    - Resource optimization
    - Error handling
    - Performance tuning
    """
    
    # Flask Configuration
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # SQLAlchemy Configuration
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_MAX_OVERFLOW = 20
    SQLALCHEMY_POOL_TIMEOUT = 30
    
    # Celery Configuration
    CELERY_CONFIG = {
        'broker_pool_limit': 10,
        'result_expires': 3600,  # 1 hour
        'task_acks_late': True,
        'task_reject_on_worker_lost': True,
        'worker_prefetch_multiplier': 1
    }
    
    # Cache Configuration
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = 'redis://localhost:6379/2'
    CACHE_DEFAULT_TIMEOUT = 300
```

### 3. Service Configurations

#### Nginx Configuration
Web server setup:

# /etc/nginx/sites-available/karhuno
server {
    listen 80;
    server_name your_domain.com;
    
    # SSL Configuration
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/your_domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your_domain.com/privkey.pem;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Content-Type-Options "nosniff";
    
    # Application Proxy
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static Files
    location /static {
        alias /opt/karhuno/app/static;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
    
    # Logging
    access_log /var/log/nginx/karhuno_access.log;
    error_log /var/log/nginx/karhuno_error.log;
}

#### Supervisor Configuration
Process management:

; /etc/supervisor/conf.d/karhuno.conf

[program:karhuno_web]
command=/opt/karhuno/venv/bin/gunicorn -w %(ENV_GUNICORN_WORKERS)s -b 127.0.0.1:8000 "app:create_app()"
directory=/opt/karhuno
user=karhuno
autostart=true
autorestart=true
startsecs=5
stopwaitsecs=60
stopasgroup=true
killasgroup=true
stdout_logfile=/var/log/karhuno/web.log
stderr_logfile=/var/log/karhuno/web.err
environment=
    FLASK_ENV="production",
    PYTHONPATH="/opt/karhuno"

[program:karhuno_worker]
command=/opt/karhuno/venv/bin/celery -A app.celery worker --loglevel=info -c %(ENV_CELERY_WORKERS)s
directory=/opt/karhuno
user=karhuno
autostart=true
autorestart=true
startsecs=5
stopwaitsecs=60
stopasgroup=true
killasgroup=true
stdout_logfile=/var/log/karhuno/worker.log
stderr_logfile=/var/log/karhuno/worker.err
environment=
    FLASK_ENV="production",
    PYTHONPATH="/opt/karhuno"

#### Redis Configuration
Cache and queue management:

# /etc/redis/redis.conf

# Memory Management
maxmemory 8gb
maxmemory-policy allkeys-lru

# Persistence
appendonly yes
appendfsync everysec

# Connection
bind 127.0.0.1
protected-mode yes
port 6379

# Logging
logfile /var/log/redis/redis.log
loglevel notice

# Performance
tcp-keepalive 300
timeout 0
tcp-backlog 511

### 4. Logging Configuration
System-wide logging setup:

# /etc/logrotate.d/karhuno
/var/log/karhuno/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 karhuno karhuno
    sharedscripts
    postrotate
        supervisorctl restart karhuno:*
    endscript
}

## Configuration Management

### 1. Version Control
Track configuration changes:

```python
config_management = {
    'version_control': {
        'track_configs': True,
        'exclude_secrets': True,
        'backup_before_change': True
    },
    'deployment': {
        'use_templates': True,
        'environment_specific': True,
        'validate_before_apply': True
    },
    'monitoring': {
        'track_changes': True,
        'alert_on_change': True,
        'audit_trail': True
    }
}
```

### 2. Security Considerations
Protect sensitive configuration:

```python
security_practices = {
    'secrets_management': {
        'use_env_vars': True,
        'encrypt_sensitive': True,
        'rotate_regularly': True
    },
    'access_control': {
        'restrict_config_access': True,
        'audit_config_changes': True,
        'separate_environments': True
    },
    'validation': {
        'check_security_settings': True,
        'validate_ssl_config': True,
        'verify_permissions': True
    }
}
```

### 3. Backup Configuration
Configure backup strategy:

```python
backup_config = {
    'database': {
        'schedule': 'daily',
        'retention': '30 days',
        'type': 'full + incremental',
        'location': 'secure_backup_server'
    },
    'configuration': {
        'schedule': 'on change',
        'retention': 'last 10 versions',
        'type': 'full',
        'location': 'version_control'
    },
    'logs': {
        'schedule': 'weekly',
        'retention': '90 days',
        'type': 'compressed',
        'location': 'log_server'
    }
}
```

## Related Topics
- [Setup Guide](setup.md)
- [Security Setup](security.md)
- [Monitoring Setup](monitoring.md)
- [System Architecture](../overview/architecture.md)