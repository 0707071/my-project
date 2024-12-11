# Prompts Overview

## Introduction

Karhuno prompts are:

- Business case specific

- Structured for consistent output

- Optimized for signal detection

- Language-aware (multilingual support)


Analysis Flow:
```text
Setup -> Configuration -> Collection -> Analysis -> Review -> Delivery
                                                      |
                                                      v
                                               Improvement -> Back to Config
```
## Prompt Components

### 1. Role Definition
Set LLM expertise and context:

```text
Example:
"You are an experienced B2B sales and marketing specialist in warehouse technology.
Your expertise includes energy efficiency, facility operations, and business signal analysis.
You understand technical specifications and their business implications."
```

### 2. Task Description
Define analysis objectives:

```text
Example:
"Analyze web pages and search results to identify potential leads for [product].
Focus on:
- Company's facility type
- Energy efficiency needs
- Scale of operations
- Decision readiness"
```

### 3. Response Format
Specify output structure:

```text
Example:
"Return results as a Python list:
[
    'Company name or N/A',
    Signal strength (0-4),
    'Revenue range',
    'Company summary',
    'Sales team notes',
    'News context'
]"
```

## Business Cases

### 1. Warehouse Sensors Case
Example implementation:

```text
Key Elements:
- Focus on energy efficiency
- Cold storage priority
- Revenue-based targeting
- Regional preferences
- Language: Russian responses

Search Queries:
- Warehouse modernization
- Energy efficiency projects
- Cold storage facilities
- Logistics center expansion
```

### 2. Construction Equipment Case
Example implementation:

```text
Key Elements:
- Physical operations focus
- Equipment usage potential
- International scope
- Website validation
- Language: English responses

Search Queries:
- Construction acquisitions
- Infrastructure projects
- Equipment fleet expansion
- Facility maintenance
```

## Search Configuration

### 1. Query Structure
Building effective queries:

```text
Components:
- Core business terms
- Action indicators
- Industry specifics
- Geographic focus

Example Set:
- "warehouse automation news"
- "logistics technology investment"
- "cold storage facility expansion"
- "energy efficiency projects"
```

### 2. Query Management
Organizing search queries:

```text
Categories:
- Direct business signals
- Industry developments
- Company activities
- Market changes

Languages:
- Primary market language
- Additional relevant languages
- Regional variations
```

## Best Practices

### 1. Prompt Development
Key considerations:

- Match business case specifics
- Include clear examples
- Define validation criteria
- Consider language requirements
- Test with sample data

### 2. Query Optimization
Search improvement:

- Monitor result quality
- Adjust based on feedback
- Include/exclude terms
- Track success patterns
- Document effective approaches

### 3. Quality Control
Maintaining standards:

- Regular prompt review
- Query effectiveness check
- Result validation
- Language accuracy
- Format consistency

## Related Topics
- [Results Structure](results.md)
- [Analysis Process](../business-processes/analysis-process.md)
- [Search Configuration](../business-processes/search-config.md)
- [Quality Metrics](../performance/metrics.md)
