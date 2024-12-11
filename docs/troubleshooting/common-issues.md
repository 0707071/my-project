# Common Issues

## Overview

This guide helps analysts resolve common issues in:
- Signal quality
- Analysis accuracy
- Processing efficiency
- Result validation

## Signal Quality Issues

### 1. Low Signal Quality
When LLM returns too many weak signals:

```text
Problem:
- Many signals with low strength (1-2)
- Vague or general matches
- Missing important details

Solution:
1. Review and improve prompt specificity:
   - Add more specific signal indicators
   - Include clear exclusion criteria
   - Provide better examples

2. Check search queries:
   - Make keywords more specific
   - Add relevant industry terms
   - Include technical specifications
```

### 2. False Positives
When LLM identifies irrelevant matches:

```text
Problem:
- Competitors marked as leads
- News about wrong topics
- Irrelevant company mentions

Solution:
1. Enhance exclusion criteria:
   - List competitor keywords
   - Define clear industry boundaries
   - Specify what's not a signal

2. Improve context understanding:
   - Add industry-specific examples
   - Clarify business relationships
   - Define market positions
```

## Analysis Issues

### 1. Inconsistent Format
When LLM responses don't follow the format:

```text
Problem:
- Missing fields in response
- Wrong data types
- Inconsistent structure

Solution:
1. Strengthen format requirements:
   - Add more format examples
   - Specify required fields
   - Include validation rules

2. Check prompt clarity:
   - Review format instructions
   - Add field descriptions
   - Show good/bad examples
```

### 2. Missing Information
When key details are not extracted:

```text
Problem:
- Missing company names
- Incomplete summaries
- Vague context

Solution:
1. Improve data extraction:
   - Specify where to look
   - Add extraction rules
   - Provide fallback options

2. Enhance context requirements:
   - Define minimum info needed
   - Add context examples
   - Specify detail level
```

## Processing Issues

### 1. Token Limits
When hitting LLM token limits:

```text
Problem:
- Truncated responses
- Incomplete analysis
- Processing errors

Solution:
1. Optimize content:
   - Focus on relevant parts
   - Remove redundant text
   - Structure data efficiently

2. Adjust batch size:
   - Split large texts
   - Process in chunks
   - Combine results later
```

### 2. Rate Limits
When hitting API rate limits:

```text
Problem:
- Failed requests
- Processing delays
- Incomplete batches

Solution:
1. Optimize processing:
   - Add request delays
   - Implement retries
   - Use batch processing

2. Manage quotas:
   - Monitor usage
   - Schedule tasks
   - Distribute load
```

## Quality Control

### 1. Validation Process
Implement quality checks:

```text
Problem:
- Missed important signals
- Quality inconsistency
- Validation overhead

Solution:
1. Use validation samples:
   - Mix known good signals
   - Check detection rate
   - Track accuracy

2. Regular reviews:
   - Check random samples
   - Document issues
   - Update prompts
```

### 2. Performance Tracking
Monitor analysis quality:

```text
Problem:
- Quality degradation
- Inconsistent results
   - Efficiency issues

Solution:
1. Track metrics:
   - Signal quality scores
   - Processing success rate
   - Analysis accuracy

2. Regular optimization:
   - Review performance
   - Update configurations
   - Refine prompts
```

## Best Practices

### 1. Regular Maintenance
Keep system optimized:

- Review and update prompts monthly
- Check search queries effectiveness
- Monitor signal quality trends
- Document successful approaches

### 2. Quality Improvement
Continuously enhance results:

- Collect analyst feedback
- Document common issues
- Share successful solutions
- Update best practices

## Related Topics
- [Analysis Process](../business-processes/analysis-process.md)
- [Prompt Structure](../prompts/structure.md)
- [Quality Metrics](../performance/metrics.md)
- [Support Guide](support.md)

