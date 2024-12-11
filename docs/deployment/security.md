# Security Setup

## Overview

Security is critical for Karhuno because:
- We handle sensitive business data
- Multiple external API integrations
- Various user access levels
- Distributed system architecture

## Security Layers

### 1. Network Security
Configure network protection:

```python
network_security = {
    'firewall': {
        'default_policy': 'deny',
        'allowed_ports': {
            'http': 80,
            'https': 443,
            'ssh': 22
        },
        'rate_limiting': {
            'ssh_attempts': '3/minute',
            'api_requests': '300/minute'
        }
    },
    'ssl': {
        'protocols': ['TLSv1.2', 'TLSv1.3'],
        'ciphers': 'HIGH:!aNULL:!MD5',
        'hsts': True,
        'cert_type': 'Let\'s Encrypt'
    }
}
```

### 2. Application Security
Secure application configuration:

```python
class SecurityConfig:
    """
    Application security settings.
    
    Key aspects:
    1. Authentication
    2. Authorization
    3. Session management
    4. Input validation
    
    Why these settings:
    - Prevent common attacks
    - Protect user data
    - Ensure secure communication
    - Track security events
    """
    
    def get_security_config(self) -> Dict[str, Any]:
        """
        Get security configuration.
        
        Settings explained:
        - CSRF protection required
        - Secure session cookies
        - Strong password policy
        - Rate limiting enabled
        """
        return {
            'auth': {
                'password_policy': {
                    'min_length': 12,
                    'complexity': True,
                    'max_age': 90
                },
                'session': {
                    'timeout': '30m',
                    'secure': True,
                    'httponly': True
                },
                'mfa': {
                    'required_roles': ['admin'],
                    'methods': ['totp', 'email']
                }
            },
            'api': {
                'rate_limit': '300/hour',
                'token_expiry': '24h',
                'require_https': True
            }
        }
```

### 3. Data Security
Protect sensitive data:

```python
data_protection = {
    'encryption': {
        'at_rest': {
            'algorithm': 'AES-256-GCM',
            'key_rotation': '90 days',
            'scope': ['database', 'backups']
        },
        'in_transit': {
            'protocol': 'TLS 1.3',
            'cert_type': 'Let\'s Encrypt',
            'scope': ['api', 'web']
        }
    },
    'data_classification': {
        'public': ['company_name', 'industry'],
        'private': ['search_patterns', 'results'],
        'sensitive': ['api_keys', 'credentials']
    }
}
```

## Access Control

### 1. User Management
Configure user access:

```python
class AccessControl:
    """
    Manages user access and permissions.
    
    Features:
    1. Role-based access
    2. Permission management
    3. Access logging
    4. Session control
    
    Example:
        control = AccessControl()
        roles = control.get_role_config()
    """
    
    def get_role_config(self) -> Dict[str, List[str]]:
        """
        Define role permissions.
        
        Roles:
        - Admin: Full access
        - Analyst: Data management
        - Client: View results
        - API: Limited access
        """
        return {
            'admin': ['all'],
            'analyst': [
                'manage_prompts',
                'review_results',
                'export_data'
            ],
            'client': [
                'view_results',
                'download_reports'
            ],
            'api': [
                'submit_search',
                'get_results'
            ]
        }
```

### 2. API Security
Secure API access:

```python
api_security = {
    'authentication': {
        'method': 'Bearer token',
        'token_type': 'JWT',
        'expiration': '24h',
        'refresh': True
    },
    'rate_limiting': {
        'default': '300/hour',
        'burst': '50/minute',
        'cleanup': '1h'
    },
    'monitoring': {
        'log_level': 'INFO',
        'track_usage': True,
        'alert_threshold': '80%'
    }
}
```

## Monitoring and Auditing

### 1. Security Monitoring
Configure security monitoring:

```python
class SecurityMonitor:
    """
    Monitors security-related events.
    
    What to monitor:
    1. Authentication attempts
    2. Permission changes
    3. Configuration updates
    4. API usage patterns
    
    Why monitor:
    - Detect threats
    - Track changes
    - Ensure compliance
    - Investigate incidents
    """
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """
        Get monitoring configuration.
        
        Monitoring areas:
        - Access attempts
        - System changes
        - API usage
        - Error patterns
        """
        return {
            'logging': {
                'security_events': 'INFO',
                'auth_attempts': 'INFO',
                'api_access': 'INFO',
                'changes': 'INFO'
            },
            'alerts': {
                'failed_auth': '5/minute',
                'api_errors': '10/minute',
                'config_changes': 'any'
            }
        }
```

### 2. Audit Trail
Configure audit logging:

```python
audit_config = {
    'events': {
        'user_access': {
            'login': True,
            'logout': True,
            'failed_attempts': True
        },
        'data_access': {
            'view': True,
            'export': True,
            'modify': True
        },
        'system_changes': {
            'configuration': True,
            'permissions': True,
            'api_keys': True
        }
    },
    'retention': {
        'audit_logs': '365 days',
        'access_logs': '90 days',
        'security_events': '180 days'
    }
}
```

## Related Topics
- [Configuration Guide](configuration.md)
- [Monitoring Setup](monitoring.md)
- [Access Control](../security/access-control.md)
- [Incident Response](../security/incidents.md) 