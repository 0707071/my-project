# Working with LLM

## LLM Integration

### Supported Models
- Primary: GPT-4o-mini
- Alternatives:
  - Claude-2
  - GPT-4
  - Anthropic Models
  - Custom LLM implementations

### Client Configuration
```python
from app.integrations.llm import LLMClient
from typing import List, Dict, Any

class LLMConfig:
    """LLM configuration settings"""
    def __init__(self, 
                 model_name: str,
                 api_keys: List[str],
                 max_retries: int = 3,
                 timeout: int = 30):
        self.model_name = model_name
        self.api_keys = api_keys
        self.max_retries = max_retries
        self.timeout = timeout
        
    @property
    def current_key(self) -> str:
        """Rotate API keys for load balancing"""
        return self.api_keys[0]
    
    def rotate_key(self):
        """Move current key to end of list"""
        self.api_keys.append(self.api_keys.pop(0))
```

## Processing Pipeline

### 1. Request Preparation
```python
def prepare_llm_request(text: str, prompt: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare request for LLM processing
    
    Args:
        text: Input text to analyze
        prompt: Prompt configuration
        
    Returns:
        Formatted request for LLM
    """
    return {
        "model": settings.LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": prompt["system_context"]
            },
            {
                "role": "user",
                "content": text
            }
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"}
    }
```

### 2. Response Processing
```python
async def process_llm_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process and validate LLM response
    
    Args:
        response: Raw LLM response
        
    Returns:
        Processed and validated response
    """
    try:
        # Extract content from response
        content = response['choices'][0]['message']['content']
        
        # Parse JSON response
        parsed = json.loads(content)
        
        # Validate required fields
        validate_response_format(parsed)
        
        return parsed
    except Exception as e:
        logging.error(f"Error processing LLM response: {str(e)}")
        raise LLMProcessingError(f"Failed to process response: {str(e)}")
```

## Error Handling

### 1. Retry Mechanism
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def llm_request_with_retry(client: LLMClient, 
                               request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute LLM request with retry mechanism
    """
    try:
        return await client.complete(request)
    except Exception as e:
        logging.warning(f"LLM request failed: {str(e)}")
        raise
```

### 2. Fallback Strategy
```python
async def process_with_fallback(text: str, 
                              prompt: Dict[str, Any],
                              config: LLMConfig) -> Dict[str, Any]:
    """
    Process text with fallback to alternative models
    """
    for model in config.fallback_models:
        try:
            client = get_llm_client(model)
            return await client.analyze(text, prompt)
        except Exception as e:
            logging.error(f"Model {model} failed: {str(e)}")
            continue
    
    raise LLMProcessingError("All models failed to process request")
```

## Performance Optimization

### 1. Batch Processing
```python
async def batch_process(texts: List[str], 
                       prompt: Dict[str, Any],
                       batch_size: int = 5) -> List[Dict[str, Any]]:
    """
    Process multiple texts in batches
    """
    results = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        tasks = [process_text(text, prompt) for text in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        results.extend(batch_results)
    return results
```

### 2. Caching
```python
from functools import lru_cache
from hashlib import sha256

@lru_cache(maxsize=1000)
def get_cached_analysis(text: str, prompt_hash: str) -> Dict[str, Any]:
    """
    Get cached analysis result
    """
    cache_key = sha256(f"{text}:{prompt_hash}".encode()).hexdigest()
    return cache.get(cache_key)
```

## Monitoring and Logging

### 1. Performance Metrics
```python
class LLMMetrics:
    """Track LLM performance metrics"""
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.total_tokens = 0
        self.response_times = []
    
    def log_request(self, 
                   response_time: float,
                   tokens_used: int,
                   success: bool):
        """Log metrics for a request"""
        self.request_count += 1
        self.total_tokens += tokens_used
        self.response_times.append(response_time)
        if not success:
            self.error_count += 1
```

### 2. Quality Monitoring
```python
def monitor_response_quality(response: Dict[str, Any], 
                           expected_format: Dict[str, Any]) -> bool:
    """
    Monitor quality of LLM responses
    
    Returns:
        True if response meets quality criteria
    """
    # Check response format
    if not validate_response_format(response, expected_format):
        return False
    
    # Check confidence scores
    if response.get('confidence_score', 0) < settings.MIN_CONFIDENCE:
        return False
    
    # Check completeness
    if not check_response_completeness(response):
        return False
    
    return True
```