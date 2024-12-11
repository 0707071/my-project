# System Architecture

## Design Philosophy

The architecture of Karhuno is built around three core principles:

1. **Reliability**: Tasks can take hours to complete
   - System must handle long-running processes
   - Network issues shouldn't fail entire tasks
   - Results must be preserved even if browser closes

2. **Scalability**: Data volume grows with each client
   - Each client adds 20-50 search queries
   - Each query generates 100-500 results
   - Analysis requires significant processing power

3. **Maintainability**: System constantly evolves
   - New data sources are regularly added
   - LLM models and prompts are updated
   - Client requirements change frequently

## High-Level Overview

System Flow:
```text
Web Interface -> Task Manager -> Search Module -> Data Storage
                            -> Analysis Module -> Data Storage
Search Module -> External APIs
Analysis Module -> LLM Services
```

### Why This Structure?
Each component is isolated to allow:
- Independent scaling
- Easier maintenance
- Parallel development
- Flexible deployment

## Core Components

### 1. Web Interface (Flask)
Selected for:
- Quick MVP development
- Easy integration with Python ecosystem
- Lightweight resource usage
- Extensive middleware support

Key features:
- Client and case management
- Search query configuration
- Prompt management
- Task monitoring
- Results visualization

[See Web Interface Details](../developer/web-interface.md)

### 2. Task Manager (Celery)
Critical for handling long-running processes:
- Tasks can run for hours
- Browser sessions may end
- Network interruptions are common
- Resource management is crucial

Features:
- Asynchronous task execution
- Automatic retries
- Progress tracking
- Resource monitoring

[See Task Management Guide](../developer/task-management.md)

### 3. Search Module
Handles data collection and preprocessing:
- XMLSTOCK API integration
- Result deduplication
- Content extraction
- Initial filtering

[See Search Module Documentation](../developer/search-module.md)

### 4. Analysis Module
Manages intelligent data processing:
- LLM integration
- Prompt handling
- Result classification
- Quality validation

[See Analysis Module Guide](../developer/analysis-module.md)

## Integration Points

### External Services

#### XMLSTOCK API
Why XMLSTOCK?
- Aggregates multiple search engines
- Handles rate limiting
- Provides consistent API
- Manages search engine updates

[See XMLSTOCK Integration Guide](../integrations/xmlstock.md)

#### LLM Services
Current setup:
- Primary: GPT-4o-mini
  - Best balance of speed/quality
  - Cost-effective for high volume
- Fallbacks:
  - Claude-2 for complex analysis
  - GPT-4 for edge cases

[See LLM Integration Guide](../integrations/llm.md)

## Data Flow

### 1. Search Process