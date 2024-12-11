# Extending the System

## Adding New Data Sources

### 1. Source Integration
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class DataSourceBase(ABC):
    """Base class for data source integrations"""
    
    @abstractmethod
    async def search(self, query: str, params: Dict[str, Any]) -> List[Dict]:
        """Execute search and return results"""
        pass
    
    @abstractmethod
    async def validate_response(self, response: Any) -> bool:
        """Validate response from the source"""
        pass

class NewDataSource(DataSourceBase):
    """Example implementation for a new data source"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
    
    async def search(self, query: str, params: Dict[str, Any]) -> List[Dict]:
        # Implementation for the new source
        pass
```

### 2. Parser Implementation
```python
from app.utils.parser_base import BaseParser

class NewSourceParser(BaseParser):
    """Parser for new data source"""
    
    def extract_text(self, html: str) -> str:
        # Custom text extraction logic
        pass
    
    def extract_metadata(self, data: Dict) -> Dict:
        # Custom metadata extraction
        pass
    
    def validate(self, parsed_data: Dict) -> bool:
        # Custom validation rules
        pass
```

## Creating Custom Pipelines

### 1. Pipeline Definition
```python
from app.pipelines.base import Pipeline
from typing import List, Dict

class CustomPipeline(Pipeline):
    """Custom data processing pipeline"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.custom_settings = config.get('custom_settings', {})
    
    async def process(self, data: List[Dict]) -> List[Dict]:
        """
        Custom processing logic
        
        Args:
            data: Input data to process
            
        Returns:
            Processed data
        """
        # Implementation of custom processing steps
        pass
    
    def validate_results(self, results: List[Dict]) -> bool:
        """Custom validation logic"""
        pass
```

### 2. Task Integration
```python
from app.tasks import celery
from app.models import CustomTask

@celery.task(bind=True)
def run_custom_pipeline(self, task_id: int):
    """Execute custom pipeline task"""
    
    task = CustomTask.query.get(task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    
    pipeline = CustomPipeline(task.config)
    results = await pipeline.process(task.input_data)
    
    # Save results
    save_custom_results(results, task_id)
```

## Implementing New Analysis Types

### 1. Analysis Module
```python
from app.analysis.base import Analyzer
from typing import Dict, Any

class CustomAnalyzer(Analyzer):
    """Custom analysis implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.analysis_params = config.get('analysis_params', {})
    
    async def analyze(self, data: Dict) -> Dict:
        """
        Perform custom analysis
        
        Args:
            data: Input data for analysis
            
        Returns:
            Analysis results
        """
        # Custom analysis implementation
        pass
    
    def format_results(self, results: Dict) -> Dict:
        """Format analysis results"""
        pass
```

### 2. LLM Integration
```python
class CustomLLMProcessor:
    """Custom LLM processing logic"""
    
    def __init__(self, model_name: str, prompt_template: str):
        self.model_name = model_name
        self.prompt_template = prompt_template
        
    async def process(self, text: str, params: Dict) -> Dict:
        """
        Process text with custom LLM logic
        
        Args:
            text: Input text
            params: Processing parameters
            
        Returns:
            Processed results
        """
        prompt = self.prepare_prompt(text, params)
        result = await self.run_llm(prompt)
        return self.parse_response(result)
```

## Adding Web Interface Features

### 1. New Routes
```python
from flask import Blueprint, render_template, jsonify
from app.models import CustomModel

custom_bp = Blueprint('custom', __name__)

@custom_bp.route('/custom/<int:id>')
@login_required
def custom_view(id):
    """Custom view handler"""
    data = CustomModel.query.get_or_404(id)
    return render_template('custom/view.html', data=data)

@custom_bp.route('/api/custom/<int:id>')
@login_required
def custom_api(id):
    """Custom API endpoint"""
    data = CustomModel.query.get_or_404(id)
    return jsonify(data.to_dict())
```

### 2. Custom Forms
```python
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired

class CustomForm(FlaskForm):
    """Custom form implementation"""
    
    name = StringField('Name', validators=[DataRequired()])
    config = TextAreaField('Configuration')
    
    def validate_config(self, field):
        """Custom config validation"""
        try:
            config_data = json.loads(field.data)
            # Custom validation logic
        except json.JSONDecodeError:
            raise ValidationError('Invalid JSON configuration')
```

## Error Handling and Logging

### 1. Custom Exceptions
```python
class CustomSourceError(Exception):
    """Custom data source error"""
    pass

class CustomProcessingError(Exception):
    """Custom processing error"""
    pass

class CustomValidationError(Exception):
    """Custom validation error"""
    pass
```

### 2. Error Handlers
```python
@custom_bp.errorhandler(CustomSourceError)
def handle_custom_source_error(error):
    """Handle custom source errors"""
    return jsonify({
        'error': 'Custom Source Error',
        'message': str(error)
    }), 400

@custom_bp.errorhandler(CustomProcessingError)
def handle_processing_error(error):
    """Handle processing errors"""
    return jsonify({
        'error': 'Processing Error',
        'message': str(error)
    }), 500
```

## Testing Extensions

### 1. Test Cases
```python
import pytest
from app.extensions.custom import CustomProcessor

def test_custom_processor():
    """Test custom processor functionality"""
    processor = CustomProcessor(config={'test': True})
    result = processor.process({'input': 'test'})
    assert result['status'] == 'success'
    assert 'output' in result

@pytest.mark.asyncio
async def test_custom_pipeline():
    """Test custom pipeline execution"""
    pipeline = CustomPipeline(config={'test': True})
    results = await pipeline.process([{'test': 'data'}])
    assert len(results) > 0
    assert all(r['processed'] for r in results)
```

### 2. Integration Tests
```python
def test_custom_integration(client, auth):
    """Test custom feature integration"""
    auth.login()
    response = client.post('/custom/process', json={
        'data': 'test',
        'config': {'test': True}
    })
    assert response.status_code == 200
    assert response.json['status'] == 'success'
```