# Security Configuration

## Overview

Security configuration in Karhuno requires careful setup because:
- Multiple integration points need protection
- Different user roles require different access levels
- API credentials must be securely managed
- System monitoring needs proper configuration

## Authentication Setup

### 1. User Authentication
Configure authentication system:

```python
auth_config = {
    'session': {
        'timeout': '30m',          # Session timeout
        'max_attempts': 5,         # Login attempts before lockout
        'lockout_duration': '15m', # Account lockout time
        'token_refresh': '15m'     # Token refresh interval
    },
    'password_policy': {
        'min_length': 12,
        'require_special': True,
        'require_numbers': True,
        'require_mixed_case': True,
        'max_age_days': 90
    },
    'mfa': {
        'required_roles': ['admin', 'developer'],
        'optional_roles': ['analyst'],
        'methods': ['totp', 'email']
    }
}
```

### 2. Role Configuration
Define role-based access:

```python
class RoleConfiguration:
    """
    Configures role-based access control.
    
    Why structured roles:
    - Clear permission boundaries
    - Easy access management
    - Audit trail support
    - Simplified maintenance
    
    Example:
        config = RoleConfiguration()
        roles = config.get_role_definitions()
    """
    
    def get_role_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Define system roles and permissions.
        
        Role hierarchy:
        1. Admin - Full system access
        2. Developer - System configuration
        3. Analyst - Data management
        4. Client - Limited view
        
        Note: Always use minimum required permissions
        """
        return {
            'admin': {
                'permissions': ['all'],
                'requires_mfa': True,
                'session_timeout': '15m',
                'audit_level': 'full'
            },
            'developer': {
                'permissions': [
                    'configure_system',
                    'view_logs',
                    'manage_workers'
                ],
                'requires_mfa': True,
                'session_timeout': '30m',
                'audit_level': 'high'
            },
            'analyst': {
                'permissions': [
                    'manage_prompts',
                    'review_results',
                    'export_data'
                ],
                'requires_mfa': False,
                'session_timeout': '1h',
                'audit_level': 'medium'
            },
            'client': {
                'permissions': [
                    'view_results',
                    'download_reports'
                ],
                'requires_mfa': False,
                'session_timeout': '2h',
                'audit_level': 'basic'
            }
        }
```

## API Security

### 1. API Key Management
Configure API security:

```python
class APIKeyManager:
    """
    Manages API credentials and security.
    
    Key features:
    1. Automatic key rotation
    2. Usage monitoring
    3. Access restrictions
    4. Audit logging
    
    Why important:
    - Prevent unauthorized access
    - Track API usage
    - Manage costs
    - Detect issues
    """
    
    def get_api_config(self) -> Dict[str, Any]:
        """
        Get API security configuration.
        
        Configuration includes:
        - Key rotation schedule
        - Usage limits
        - Access controls
        - Monitoring rules
        
        Example:
        - Rotate keys every 30 days
        - Monitor usage patterns
        - Alert on anomalies
        """
        return {
            'rotation': {
                'schedule': '30d',
                'overlap_period': '24h',
                'notification_before': '7d'
            },
            'limits': {
                'rate_limit': '100/minute',
                'daily_quota': 10000,
                'max_concurrent': 10
            },
            'monitoring': {
                'log_level': 'detailed',
                'alert_threshold': '80%',
                'track_patterns': True
            }
        }
```

### 2. Request Security
Configure request handling:

```python
request_security = {
    'validation': {
        'input_sanitization': True,
        'schema_validation': True,
        'size_limits': {
            'max_request_size': '10MB',
            'max_field_length': '1MB'
        }
    },
    'rate_limiting': {
        'window_size': '1m',
        'max_requests': 100,
        'burst_size': 20
    },
    'ip_control': {
        'whitelist_enabled': True,
        'blacklist_enabled': True,
        'geo_restrictions': True
    }
}
```

## Data Security

### 1. Encryption Configuration
Configure data encryption:

```python
class EncryptionConfig:
    """
    Configures system-wide encryption settings.
    
    Protection levels:
    1. Database encryption
    2. File encryption
    3. Network encryption
    4. Memory protection
    
    Why comprehensive:
    - Protect all data states
    - Meet compliance requirements
    - Prevent data leaks
    """
    
    def get_encryption_config(self) -> Dict[str, Any]:
        """
        Get encryption configuration.
        
        Settings for:
        - Key management
        - Algorithm selection
        - Rotation policies
        - Backup protection
        """
        return {
            'algorithms': {
                'data_at_rest': 'AES-256-GCM',
                'data_in_transit': 'TLS 1.3',
                'key_encryption': 'RSA-4096'
            },
            'key_management': {
                'rotation_period': '90d',
                'key_derivation': 'PBKDF2',
                'master_key_backup': True
            },
            'scope': {
                'database': True,
                'file_system': True,
                'api_payload': True,
                'backups': True
            }
        }
```

## Monitoring Configuration

### 1. Security Monitoring
Configure security monitoring:

```python
monitoring_config = {
    'logging': {
        'security_events': {
            'level': 'INFO',
            'retention': '90d',
            'alert_on': [
                'authentication_failure',
                'permission_violation',
                'unusual_activity'
            ]
        },
        'audit_trail': {
            'level': 'DEBUG',
            'retention': '365d',
            'include_details': True
        }
    },
    'alerts': {
        'channels': ['email', 'slack'],
        'severity_levels': ['info', 'warning', 'critical'],
        'notification_rules': {
            'immediate': ['critical'],
            'daily_digest': ['warning'],
            'weekly_summary': ['info']
        }
    }
}
```

## Related Topics
- [Security Overview](overview.md)
- [Best Practices](best-practices.md)
- [System Configuration](../deployment/configuration.md)
- [Monitoring Setup](../deployment/monitoring.md) 