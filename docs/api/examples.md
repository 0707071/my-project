# API Examples

## Overview

This guide provides practical examples of:
- Common API workflows
- Integration patterns
- Error handling
- Best practices

## Search Configuration

### 1. Create Search Configuration
Example of setting up a search:

```python
import requests
import json

def create_search_config():
    url = "https://api.karhuno.com/v1/search/config"
    
    # Configuration data
    config = {
        "name": "Warehouse Tech Search",
        "description": "Search for warehouse automation news",
        "queries": [
            "warehouse automation",
            "logistics technology",
            "storage automation"
        ],
        "filters": {
            "date_from": "2024-01-01",
            "languages": ["en"],
            "regions": ["europe", "north_america"],
            "exclude_domains": ["competitor1.com", "competitor2.com"]
        },
        "schedule": "daily"
    }
    
    # Headers with authentication
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=config, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error creating search config: {e}")
        return None
```

### 2. Start Search Process
Execute a configured search:

```python
def execute_search(config_id):
    url = f"https://api.karhuno.com/v1/search/execute"
    
    execution_params = {
        "config_id": config_id,
        "priority": "normal",
        "notify_on_completion": True
    }
    
    try:
        response = requests.post(url, json=execution_params, headers=headers)
        if response.status_code == 202:
            job_id = response.json()["job_id"]
            return monitor_search_progress(job_id)
        else:
            print(f"Error starting search: {response.json()}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error executing search: {e}")
        return None

def monitor_search_progress(job_id):
    url = f"https://api.karhuno.com/v1/search/status/{job_id}"
    
    while True:
        try:
            response = requests.get(url, headers=headers)
            status = response.json()["status"]
            
            if status == "completed":
                return response.json()["results"]
            elif status == "failed":
                print(f"Search failed: {response.json()['error']}")
                return None
            
            time.sleep(5)  # Poll every 5 seconds
        except requests.exceptions.RequestException as e:
            print(f"Error monitoring search: {e}")
            return None
```

## Analysis Configuration

### 1. Create Analysis Prompt
Set up analysis parameters:

```python
def create_analysis_prompt():
    url = "https://api.karhuno.com/v1/analysis/prompt"
    
    prompt_config = {
        "name": "Warehouse Tech Analysis",
        "description": "Analyze warehouse automation signals",
        "prompt_text": """
        Analyze the text for warehouse automation signals.
        Focus on:
        - Technology implementation
        - Automation projects
        - Efficiency improvements
        """,
        "output_format": {
            "company_name": "str",
            "signal_strength": "int",
            "summary": "str",
            "details": "str"
        },
        "examples": [
            {
                "input": "Company X implements new warehouse system...",
                "output": {
                    "company_name": "Company X",
                    "signal_strength": 4,
                    "summary": "Major automation project",
                    "details": "Full warehouse system upgrade..."
                }
            }
        ]
    }
    
    try:
        response = requests.post(url, json=prompt_config, headers=headers)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error creating prompt: {e}")
        return None
```

### 2. Run Analysis
Process search results:

```python
def analyze_results(prompt_id, search_results):
    url = "https://api.karhuno.com/v1/analysis/execute"
    
    analysis_config = {
        "prompt_id": prompt_id,
        "data": search_results,
        "batch_size": 100,
        "priority": "normal"
    }
    
    try:
        response = requests.post(url, json=analysis_config, headers=headers)
        if response.status_code == 202:
            job_id = response.json()["job_id"]
            return monitor_analysis_progress(job_id)
        else:
            print(f"Error starting analysis: {response.json()}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error executing analysis: {e}")
        return None
```

## Results Management

### 1. Retrieve Results
Get analysis results:

```python
def get_results(job_id, filters=None):
    url = f"https://api.karhuno.com/v1/results/{job_id}"
    
    params = {
        "page": 1,
        "per_page": 100,
        "min_signal_strength": 3,
        **filters if filters else {}
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        return response.json()["results"]
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving results: {e}")
        return None
```

### 2. Export Results
Export to different formats:

```python
def export_results(job_id, format="csv"):
    url = f"https://api.karhuno.com/v1/results/export/{job_id}"
    
    params = {
        "format": format,
        "fields": [
            "company_name",
            "signal_strength",
            "summary",
            "details"
        ]
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        with open(f"results.{format}", "wb") as f:
            f.write(response.content)
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error exporting results: {e}")
        return False
```

## Error Handling

### 1. Robust Request Handler
Example of robust API interaction:

```python
def make_api_request(method, url, **kwargs):
    retries = 3
    backoff_factor = 2
    
    for attempt in range(retries):
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                raise
            
            if hasattr(e.response, 'status_code'):
                if e.response.status_code in [429, 503]:  # Rate limit or service unavailable
                    wait_time = backoff_factor ** attempt
                    time.sleep(wait_time)
                    continue
                elif e.response.status_code == 401:  # Token expired
                    refresh_token()
                    kwargs['headers']['Authorization'] = f"Bearer {access_token}"
                    continue
            
            raise
```

## Complete Workflow

### 1. Full Process Example
Combining all steps:

```python
def run_analysis_workflow():
    try:
        # Create search configuration
        search_config = create_search_config()
        if not search_config:
            return None
            
        # Execute search
        search_results = execute_search(search_config["id"])
        if not search_results:
            return None
            
        # Create analysis prompt
        prompt = create_analysis_prompt()
        if not prompt:
            return None
            
        # Run analysis
        analysis_results = analyze_results(prompt["id"], search_results)
        if not analysis_results:
            return None
            
        # Export results
        export_results(analysis_results["job_id"], format="csv")
        
        return True
        
    except Exception as e:
        print(f"Workflow failed: {e}")
        return None
```

## Related Topics
- [API Overview](overview.md)
- [API Authentication](authentication.md)
- [API Endpoints](endpoints.md)
- [Error Handling](../troubleshooting/common-issues.md) 