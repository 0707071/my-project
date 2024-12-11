# Analysis Results Structure

## Overview

Analysis results in Karhuno are:
- Raw LLM responses in Python list format
- Parsed into structured table data
- Customized for each business case
- Validated against defined rules

## Response Format

### 1. Basic Structure
LLM returns a Python list string that is parsed into columns:

```text
Example raw response:
["Company Name", 4, "up to 1000M", "Company description...", "Sales notes...", "News context..."]

Becomes table row:
| Company | Signal Strength | Revenue | Description | Sales Notes | Context |
|---------|----------------|----------|-------------|-------------|----------|
| Company Name | 4 | up to 1000M | Company... | Sales... | News... |
```

### 2. Case-Specific Elements
Response elements vary by business case:

```text
Warehouse Sensors Case:
- Company name (required)
- Signal strength (0-4)
- Revenue range
- Company summary in Russian
- Sales team notes in Russian
- News context in Russian

Construction Equipment Case:
- Company name (required)
- Potential rating (0-4)
- Sales notes in English
- Company description
- Revenue estimate
- Country
- Website
- Assumed website
```

### 3. Common Elements
While formats vary, some elements are standard:
- Company identification
- Signal/potential strength
- Revenue information
- Business context
- Sales guidance

## Business Case Variations

### 1. Time Sensitivity
Different importance by case:

```text
Office Design:
- Timing is critical
- Project windows are short
- Immediate action needed

Equipment Sales:
- Longer sales cycles
- Timing less critical
- Focus on proper qualification
```

### 2. Geographic Focus
Location importance varies:

```text
Local Services:
- Region is critical
- Physical presence needed
- Local context important

Global Products:
- Wider geography
- Remote sales possible
- International context
```

## Data Processing

### 1. Response Parsing
Converting LLM output to data:

```text
1. LLM returns string in format: ["elem1", "elem2", ...]
2. String is parsed into Python list
3. List elements map to table columns
4. Column names match prompt output format
```

### 2. Validation Rules
Basic validation principles:

```text
Required Elements:
- Company name (or N/A)
- Signal strength (numeric)
- Revenue information
- Business context

Format Rules:
- Signal strength must be 0-4
- Revenue in defined ranges
- Text fields within length limits
```

## Best Practices

### 1. Format Definition
When defining output format:
- Match columns to business needs
- Keep consistent order
- Include all required fields
- Consider data processing needs

### 2. Quality Control
Ensure data quality:
- Define clear validation rules
- Check for required elements
- Validate numeric ranges
- Verify text formatting

## Related Topics
- [Prompt Structure](structure.md)
- [Analysis Process](../business-processes/analysis-process.md)
- [Data Pipeline](../overview/data-pipeline.md)
- [API Examples](../api/examples.md)