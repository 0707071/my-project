# Core Functionality

## Search System

### XMLSTOCK Integration
```python
from app.integrations.xmlstock import XMLStockClient

client = XMLStockClient(api_key=settings.XMLSTOCK_API_KEY)

async def fetch_search_results(query: str, params: dict) -> list:
    """
    Fetch search results from XMLSTOCK API
    
    Args:
        query: Search query string
        params: Search parameters including:
            - days_back: int
            - results_per_page: int
            - num_pages: int
    
    Returns:
        List of search results
    """
    try:
        results = await client.search(
            query=query,
            days_back=params['days_back'],
            results_per_page=params['results_per_page'],
            num_pages=params['num_pages']
        )
        return results
    except XMLStockAPIError as e:
        logging.error(f"XMLSTOCK API error: {str(e)}")
        raise
```

### Data Cleaning
```python
from app.utils.cleaners import clean_html, remove_duplicates

def clean_search_results(results: list) -> list:
    """
    Clean and deduplicate search results
    
    Args:
        results: Raw search results
        
    Returns:
        Cleaned and deduplicated results
    """
    # Remove HTML and extract text
    cleaned = [clean_html(item['content']) for item in results]
    
    # Remove duplicates
    unique = remove_duplicates(cleaned, threshold=0.85)
    
    return unique
```

## LLM Processing

### Client Configuration
```python
from app.integrations.llm import LLMClient

def get_llm_client(model_name: str, config: dict) -> LLMClient:
    """
    Get configured LLM client
    
    Args:
        model_name: Name of the model to use
        config: Configuration parameters
    
    Returns:
        Configured LLM client
    """
    return LLMClient(
        model_name=model_name,
        api_keys=config['api_keys'],
        max_retries=config.get('max_retries', 3)
    )
```

### Prompt Processing
```python
async def process_with_llm(text: str, prompt: str, output_format: dict) -> dict:
    """
    Process text with LLM using given prompt
    
    Args:
        text: Text to analyze
        prompt: Analysis prompt
        output_format: Expected output format
    
    Returns:
        Processed results in specified format
    """
    client = get_llm_client(
        model_name="gpt-4o-mini",
        config=settings.LLM_CONFIG
    )
    
    try:
        result = await client.analyze(
            text=text,
            prompt=prompt,
            output_format=output_format
        )
        return result
    except LLMError as e:
        logging.error(f"LLM processing error: {str(e)}")
        raise
```

## Task Management

### Task Queue
```python
from app.tasks import celery
from app.models import SearchTask, SearchResult

@celery.task(bind=True)
def run_search_task(self, task_id: int):
    """
    Execute search and analysis task
    
    Args:
        task_id: ID of the SearchTask
    """
    task = SearchTask.query.get(task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")
        
    try:
        # Update task status
        task.status = 'running'
        db.session.commit()
        
        # Execute search
        results = await fetch_and_process_search(task)
        
        # Store results
        save_search_results(results, task_id)
        
        # Update task status
        task.status = 'completed'
        db.session.commit()
        
    except Exception as e:
        task.status = 'failed'
        task.error = str(e)
        db.session.commit()
        raise
```

### Result Processing
```python
def save_search_results(results: list, task_id: int):
    """
    Save processed search results
    
    Args:
        results: List of processed results
        task_id: Associated task ID
    """
    for result in results:
        search_result = SearchResult(
            task_id=task_id,
            content=result['content'],
            analysis=result['analysis'],
            metadata=result['metadata']
        )
        db.session.add(search_result)
    
    db.session.commit()
```

## Data Models

### Core Models
- `User`: User management
- `Client`: Client information
- `SearchQuery`: Search configuration
- `Prompt`: Analysis prompts
- `SearchTask`: Task execution
- `SearchResult`: Search results

### Model Relationships
```python
class SearchTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    search_query_id = db.Column(db.Integer, db.ForeignKey('search_query.id'))
    prompt_id = db.Column(db.Integer, db.ForeignKey('prompt.id'))
    
    # Relationships
    client = db.relationship('Client', backref='tasks')
    search_query = db.relationship('SearchQuery', backref='tasks')
    prompt = db.relationship('Prompt', backref='tasks')
    results = db.relationship('SearchResult', backref='task')
```

## Web Interface

### Route Handlers
```python
@main.route('/tasks/<int:task_id>')
@login_required
def task_status(task_id):
    """
    Task status page handler
    """
    task = SearchTask.query.get_or_404(task_id)
    return render_template(
        'tasks/status.html',
        task=task
    )
```

### WebSocket Updates
```python
@socketio.on('connect', namespace='/task-status')
def handle_connect():
    """
    Handle WebSocket connection
    """
    if not current_user.is_authenticated:
        return False
    
    join_room(f'user_{current_user.id}')

def send_task_update(task_id: int, status: str, data: dict = None):
    """
    Send task update via WebSocket
    """
    socketio.emit(
        'task_update',
        {
            'task_id': task_id,
            'status': status,
            'data': data
        },
        namespace='/task-status'
    )
```