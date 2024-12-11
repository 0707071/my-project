# API Overview

## Introduction

Karhuno API provides:
- Search configuration management
- Analysis process control
- Result retrieval and filtering
- System monitoring

> **Important Note**: While currently used internally, the API is being designed for SaaS transition. All endpoints, documentation, and interfaces should be developed with external users in mind, focusing on:
> - Clear, self-service workflows
> - Robust error handling and guidance
> - Comprehensive documentation
> - Secure multi-tenant architecture
> - User-friendly interfaces

## Core Concepts

### 1. Authentication
API uses token-based authentication:

```python
auth_flow = {
    'method': 'Bearer token',
    'format': 'JWT',
    'expiration': '24h',
    'scope_based': True,
    'refresh_enabled': True
}
```

### 2. Rate Limiting
Default API limits:

```python
rate_limits = {
    'search': {
        'requests': '100/minute',
        'data_volume': '10MB/request'
    },
    'analysis': {
        'requests': '50/minute',
        'batch_size': '1000 items'
    },
    'results': {
        'requests': '300/minute',
        'data_volume': '50MB/request'
    }
}
```

### 3. Response Format
Standard response structure:

```python
response_format = {
    'success': bool,
    'data': {
        'results': List[Dict],
        'metadata': Dict
    },
    'error': {
        'code': str,
        'message': str,
        'details': Dict
    },
    'pagination': {
        'page': int,
        'per_page': int,
        'total': int
    }
}
```

## API Components

### 1. Search API
Manage search configurations:

```python
search_endpoints = {
    'configuration': {
        'create': 'POST /api/v1/search/config',
        'update': 'PUT /api/v1/search/config/{id}',
        'delete': 'DELETE /api/v1/search/config/{id}',
        'list': 'GET /api/v1/search/config'
    },
    'execution': {
        'start': 'POST /api/v1/search/execute',
        'status': 'GET /api/v1/search/status/{id}',
        'stop': 'POST /api/v1/search/stop/{id}'
    }
}
```

### 2. Analysis API
Control analysis process:

```python
analysis_endpoints = {
    'prompts': {
        'create': 'POST /api/v1/analysis/prompt',
        'update': 'PUT /api/v1/analysis/prompt/{id}',
        'delete': 'DELETE /api/v1/analysis/prompt/{id}',
        'list': 'GET /api/v1/analysis/prompt'
    },
    'execution': {
        'start': 'POST /api/v1/analysis/execute',
        'status': 'GET /api/v1/analysis/status/{id}',
        'stop': 'POST /api/v1/analysis/stop/{id}'
    }
}
```

### 3. Results API
Manage analysis results:

```python
results_endpoints = {
    'retrieval': {
        'get': 'GET /api/v1/results/{id}',
        'list': 'GET /api/v1/results',
        'export': 'GET /api/v1/results/export/{id}'
    },
    'filtering': {
        'apply': 'POST /api/v1/results/filter',
        'save': 'POST /api/v1/results/filter/save',
        'load': 'GET /api/v1/results/filter/{id}'
    }
}
```

## Error Handling

### 1. Error Codes
Standard error responses:

```python
error_codes = {
    'authentication': {
        '401': 'Invalid or missing token',
        '403': 'Insufficient permissions'
    },
    'validation': {
        '400': 'Invalid request format',
        '422': 'Invalid data provided'
    },
    'resource': {
        '404': 'Resource not found',
        '409': 'Resource conflict'
    },
    'server': {
        '500': 'Internal server error',
        '503': 'Service unavailable'
    }
}
```

### 2. Error Response
Example error structure:

```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid search configuration",
        "details": {
            "field": "keywords",
            "reason": "Cannot be empty"
        }
    }
}
```

## Best Practices

### 1. Rate Limiting
Handle rate limits properly:

```python
rate_limit_handling = {
    'monitoring': {
        'track_limits': True,
        'check_headers': True,
        'implement_backoff': True
    },
    'optimization': {
        'batch_requests': True,
        'cache_responses': True,
        'distribute_load': True
    }
}
```

### 2. Error Handling
Implement robust error handling:

```python
error_handling = {
    'retry_strategy': {
        'max_attempts': 3,
        'backoff_factor': 2,
        'retry_codes': [500, 502, 503, 504]
    },
    'logging': {
        'log_errors': True,
        'include_context': True,
        'alert_on_critical': True
    }
}
```

## Related Topics
- [API Authentication](authentication.md)
- [API Endpoints](endpoints.md)
- [API Examples](examples.md)
- [System Architecture](../overview/architecture.md) 