# Monitoring Setup

## Overview

Monitoring is essential for Karhuno because:
- Multiple system components need tracking
- Performance affects analysis quality
- Resource usage impacts costs
- Early problem detection is critical

## Monitoring Components

### 1. System Metrics
Track system performance:

```python
system_metrics = {
    'resources': {
        'cpu': {
            'usage_percent': 'Per process',
            'load_average': '1m, 5m, 15m',
            'alert_threshold': '80%'
        },
        'memory': {
            'usage_percent': 'Per process',
            'available': 'System-wide',
            'alert_threshold': '85%'
        },
        'disk': {
            'usage_percent': 'Per mount',
            'io_stats': 'Read/Write',
            'alert_threshold': '90%'
        }
    },
    'network': {
        'bandwidth': 'In/Out per interface',
        'connections': 'Active/Total',
        'latency': 'Per endpoint'
    }
}
```

### 2. Application Metrics
Monitor application performance:

```python
class ApplicationMonitor:
    """
    Monitors application performance.
    
    Key metrics:
    1. Response times
    2. Error rates
    3. Request volumes
    4. Queue lengths
    
    Why monitor:
    - Track user experience
    - Identify bottlenecks
    - Plan capacity
    - Detect issues
    """
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get application metrics.
        
        Metrics include:
        - API response times
        - Database query times
        - Cache hit rates
        - Error frequencies
        """
        return {
            'web': {
                'response_time': self._get_response_stats(),
                'error_rate': self._get_error_stats(),
                'active_users': self._get_user_count()
            },
            'api': {
                'requests_per_minute': self._get_request_rate(),
                'average_latency': self._get_latency_stats(),
                'error_count': self._get_api_errors()
            }
        }
```

### 3. Process Monitoring
Track worker processes:

```python
process_monitoring = {
    'celery': {
        'workers': {
            'active_tasks': 'Current count',
            'queue_length': 'Pending tasks',
            'processing_time': 'Per task'
        },
        'queues': {
            'size': 'Per queue',
            'throughput': 'Tasks/minute',
            'latency': 'Queue time'
        }
    },
    'gunicorn': {
        'workers': {
            'count': 'Active workers',
            'requests': 'Per worker',
            'memory': 'Per worker'
        }
    }
}
```

## Performance Tracking

### 1. Database Monitoring
Track database performance:

```python
class DatabaseMonitor:
    """
    Monitors database performance.
    
    What to monitor:
    1. Query performance
    2. Connection usage
    3. Cache efficiency
    4. Resource usage
    
    Why important:
    - Often the bottleneck
    - Critical for scaling
    - Impact on response time
    """
    
    def get_db_metrics(self) -> Dict[str, Any]:
        """
        Get database metrics.
        
        Key areas:
        - Query times
        - Connection pools
        - Cache hits
        - Lock waits
        """
        return {
            'performance': {
                'query_time': self._get_query_stats(),
                'connection_usage': self._get_connection_stats(),
                'cache_hit_ratio': self._get_cache_stats()
            },
            'resources': {
                'cpu_usage': self._get_cpu_stats(),
                'memory_usage': self._get_memory_stats(),
                'disk_io': self._get_io_stats()
            }
        }
```

### 2. API Monitoring
Track external API usage:

```python
api_monitoring = {
    'xmlstock': {
        'requests': {
            'success_rate': 'Percentage',
            'error_types': 'Categorized',
            'response_time': 'Average'
        },
        'limits': {
            'usage': 'Current/Total',
            'reset_time': 'Next reset',
            'remaining': 'Available calls'
        }
    },
    'openai': {
        'usage': {
            'tokens': 'Used/Limit',
            'cost': 'Per request',
            'models': 'Usage by model'
        },
        'performance': {
            'latency': 'Response time',
            'success_rate': 'Completion rate',
            'error_types': 'Categorized'
        }
    }
}
```

## Alerting System

### 1. Alert Configuration
Configure monitoring alerts:

```python
alert_config = {
    'severity_levels': {
        'critical': {
            'response_time': 'Immediate',
            'notification': ['email', 'sms', 'slack'],
            'auto_actions': True
        },
        'warning': {
            'response_time': '15m',
            'notification': ['email', 'slack'],
            'auto_actions': False
        },
        'info': {
            'response_time': '1h',
            'notification': ['email'],
            'auto_actions': False
        }
    },
    'thresholds': {
        'system': {
            'cpu': '80%',
            'memory': '85%',
            'disk': '90%'
        },
        'application': {
            'error_rate': '5%',
            'response_time': '2s',
            'queue_length': 1000
        }
    }
}
```

### 2. Response Procedures
Define alert responses:

```python
response_procedures = {
    'high_load': [
        'Check system metrics',
        'Identify bottlenecks',
        'Scale resources if needed',
        'Review recent changes'
    ],
    'high_error_rate': [
        'Check error logs',
        'Identify error patterns',
        'Review recent deployments',
        'Consider rollback'
    ],
    'api_issues': [
        'Check API status',
        'Review rate limits',
        'Check credentials',
        'Switch to backup if available'
    ]
}
```

## Related Topics
- [Performance Metrics](../performance/metrics.md)
- [System Configuration](configuration.md)
- [Troubleshooting Guide](../troubleshooting/index.md)
- [Scaling Guide](../performance/scaling.md) 