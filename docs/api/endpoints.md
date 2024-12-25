# API Endpoints

## Overview

Karhuno API includes:
- Internal service endpoints
- External API integrations
- Utility endpoints

> **SaaS Readiness**: All endpoints are designed with future SaaS deployment in mind:
> - RESTful design for easy integration
> - Consistent error handling
> - Clear validation rules
> - Multi-tenant support
> - Rate limiting per client
> - Detailed response metadata

## External API Integration

### 1. XMLStock API
Integration for data collection:

```python
xmlstock_endpoints = {
    'search': {
        'method': 'POST',
        'url': '/api/v1/external/xmlstock/search',
        'params': {
            'query': 'str',
            'filters': 'Dict[str, Any]',
            'limit': 'int',
            'offset': 'int'
        },
        'response': {
            'results': 'List[Dict]',
            'total': 'int',
            'next_token': 'Optional[str]'
        },
        'rate_limits': {
            'requests': '100/minute',
            'daily_quota': '10000'
        }
    },
    'status': {
        'method': 'GET',
        'url': '/api/v1/external/xmlstock/status',
        'response': {
            'quota_used': 'int',
            'quota_remaining': 'int',
            'reset_time': 'datetime'
        }
    }
}
```

Example request:
```json
{
    "query": "warehouse automation news",
    "filters": {
        "date_from": "2024-01-01",
        "date_to": "2024-02-01",
        "language": "en",
        "regions": ["europe", "north_america"]
    },
    "limit": 100
}
```

### 2. OpenAI API
Integration for analysis:

```python
openai_endpoints = {
    'analyze': {
        'method': 'POST',
        'url': '/api/v1/external/openai/analyze',
        'params': {
            'text': 'str',
            'prompt': 'str',
            'model': 'str',
            'temperature': 'float',
            'max_tokens': 'int'
        },
        'response': {
            'analysis': 'Dict[str, Any]',
            'tokens_used': 'int',
            'model_used': 'str'
        },
        'rate_limits': {
            'tokens_per_minute': '100000',
            'requests_per_minute': '500'
        }
    },
    'status': {
        'method': 'GET',
        'url': '/api/v1/external/openai/status',
        'response': {
            'available_models': 'List[str]',
            'quota_used': 'float',
            'quota_remaining': 'float'
        }
    }
}
```

Example request:
```json
{
    "text": "Your text here",
    "model": "gpt-4o-mini",
    "prompt": "Analyze this text for business signals...",
    "temperature": 0.7,
    "max_tokens": 500
}
```

## Internal Endpoints

### 1. Search Configuration
Manage search settings:

```python
search_config_endpoints = {
    'create': {
        'method': 'POST',
        'url': '/api/v1/search/config',
        'body': {
            'name': 'str',
            'description': 'str',
            'queries': 'List[str]',
            'filters': 'Dict[str, Any]',
            'schedule': 'Optional[str]'
        }
    },
    'update': {
        'method': 'PUT',
        'url': '/api/v1/search/config/{id}',
        'body': {
            'queries': 'List[str]',
            'filters': 'Dict[str, Any]',
            'active': 'bool'
        }
    },
    'delete': {
        'method': 'DELETE',
        'url': '/api/v1/search/config/{id}'
    }
}
```

### 2. Analysis Configuration
Manage analysis settings:

```python
analysis_config_endpoints = {
    'prompt': {
        'create': {
            'method': 'POST',
            'url': '/api/v1/analysis/prompt',
            'body': {
                'name': 'str',
                'description': 'str',
                'prompt_text': 'str',
                'output_format': 'Dict[str, str]',
                'examples': 'List[Dict]'
            }
        },
        'update': {
            'method': 'PUT',
            'url': '/api/v1/analysis/prompt/{id}',
            'body': {
                'prompt_text': 'str',
                'output_format': 'Dict[str, str]',
                'active': 'bool'
            }
        }
    }
}
```

### 3. Results Management
Handle analysis results:

```python
results_endpoints = {
    'retrieve': {
        'method': 'GET',
        'url': '/api/v1/results',
        'params': {
            'search_id': 'Optional[int]',
            'date_from': 'Optional[str]',
            'date_to': 'Optional[str]',
            'status': 'Optional[str]',
            'page': 'int',
            'per_page': 'int'
        }
    },
    'export': {
        'method': 'GET',
        'url': '/api/v1/results/export',
        'params': {
            'format': 'str',  # csv, xlsx
            'fields': 'List[str]',
            'filters': 'Dict[str, Any]'
        }
    }
}
```

## Utility Endpoints

### 1. Health Check
Monitor system status:

```python
health_endpoints = {
    'status': {
        'method': 'GET',
        'url': '/api/v1/health',
        'response': {
            'status': 'str',
            'components': {
                'database': 'str',
                'cache': 'str',
                'external_apis': 'Dict[str, str]'
            },
            'version': 'str'
        }
    }
}
```

### 2. Metrics
Monitor system metrics:

```python
metrics_endpoints = {
    'system': {
        'method': 'GET',
        'url': '/api/v1/metrics/system',
        'response': {
            'cpu_usage': 'float',
            'memory_usage': 'float',
            'disk_usage': 'float',
            'api_latency': 'Dict[str, float]'
        }
    }
}
```

## Related Topics
- [API Overview](overview.md)
- [API Authentication](authentication.md)
- [API Examples](examples.md)
- [External Integrations](../overview/integrations.md) 