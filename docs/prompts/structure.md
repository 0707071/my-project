# Prompt Structure Guide

## Overview

A well-structured prompt is critical for effective signal analysis because:
- It guides the LLM in understanding the business context
- Ensures consistent and structured responses
- Helps filter out irrelevant information
- Makes analysis results actionable for sales teams

## Key Components

### 1. Role and Context
Define who the LLM should be and what expertise it should have:

```text
Example:
You are a B2B sales and marketing specialist in [industry].
Your expertise includes [specific areas].
You understand [technical aspects] and their business implications.
```

Key points:
- Be specific about the industry expertise
- Define relevant technical knowledge
- Set the business context
- Explain why this expertise matters

### 2. Task Description
Clearly explain what needs to be analyzed:

```text
Example:
Your task is to analyze [content type] to identify potential leads for [product/service].
Key product features that matter:
- Feature A and its business benefit
- Feature B and its business benefit
- Feature C and its business benefit
```

Important aspects:
- Define the analysis objective
- Highlight key product features
- Connect features to business benefits
- Set clear expectations

### 3. Analysis Framework
Provide clear criteria for analysis:

```text
Example:
Key Analysis Points:
- What to look for in the text
- How to identify company names
- What revenue ranges to consider
- What industries to focus on
- What to exclude
```

Best practices:
- List specific indicators to look for
- Define clear exclusion criteria
- Provide revenue/size thresholds
- Explain priority factors

### 4. Signal Definition
Define what constitutes a valuable signal:

```text
Example:
Signals Indicating Interest:
- Signal A (with explanation)
- Signal B (with explanation)
- Signal C (with explanation)

Special Focus:
- Priority customer types
- Key geographical regions
- Specific facility types
- Business situations
```

Remember to:
- Define both positive and negative signals
- Explain why each signal matters
- Provide context for prioritization
- Include industry-specific nuances

### 5. Response Format
Specify exactly how the LLM should structure its response:

```text
Example:
Return results as a list:
["Company name", 
 signal_strength (0-4), 
 "revenue_range",
 "company_summary",
 "sales_notes",
 "context_summary"]
```

Important:
- Use consistent formats
- Define all fields clearly
- Provide value ranges
- Include examples

### 6. Examples
Provide clear examples of good and bad responses:

```text
Good example:
["TechCorp", 4, "up to 1000M", "Detailed summary...", "Specific sales approach...", "Relevant context..."]

Bad example:
["Unknown", 1, "unknown", "Limited info...", "No clear approach...", "Vague context..."]
```

Why examples matter:
- Show expected quality level
- Demonstrate format compliance
- Illustrate decision-making
- Help calibrate responses

## Best Practices

### 1. Clarity
- Use simple, clear language
- Break down complex criteria
- Provide specific examples
- Explain why things matter

### 2. Consistency
- Use consistent terminology
- Maintain format throughout
- Keep scoring scales uniform
- Use standard categories

### 3. Completeness
- Include all necessary context
- Define all required fields
- Explain all criteria
- Provide fallback options

### 4. Quality Control
- Define minimum quality standards
- Include validation criteria
- Specify required elements
- Set clear boundaries

## Common Mistakes to Avoid

1. **Vague Instructions**
   - Too general criteria
   - Unclear priorities
   - Undefined terms
   - Missing context

2. **Format Issues**
   - Inconsistent structure
   - Unclear field definitions
   - Missing examples
   - Ambiguous scales

3. **Context Problems**
   - Insufficient background
   - Missing industry context
   - Unclear priorities
   - Undefined scope

## Related Topics
- [Analysis Process](../business-processes/analysis-process.md)
- [Quality Metrics](../performance/metrics.md)
- [Best Practices](../best-practices/index.md)
- [Case Studies](../guides/use-cases.md)