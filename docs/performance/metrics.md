# Performance Metrics

## Overview

Performance metrics in Karhuno are case-specific and focus on:
- Processing efficiency
- Signal quality
- System scalability

## Processing Metrics

### 1. Collection Performance
```python
collection_metrics = {
    'raw_signals': {
        'target': 1000,  # signals per collection
        'time_limit': '30m',  # maximum collection time
        'parallel_processes': 4  # concurrent collectors
    },
    'filtering_stats': {
        'unparseable_rate': 'failed_parse / total_collected',
        'duplicate_rate': 'duplicates / total_collected',
        'clean_signals': 'valid_signals / total_collected'
    }
}
```

### 2. Cleaning Performance
Different cleaning strategies for different sources:

```python
class CleaningMetrics:
    """
    Tracks cleaning performance by source type.
    
    Key aspects:
    1. Source-specific deduplication
    2. Content extraction success
    3. Processing speed
    
    Example:
        metrics = CleaningMetrics()
        job_stats = metrics.get_stats('job_boards')
    """
    
    def get_cleaning_strategy(self, source_type: str) -> Dict[str, Any]:
        """
        Get source-specific cleaning metrics.
        
        Strategies:
        - Job boards: URL-based deduplication only
        - News: Content similarity check
        - Social media: Mixed approach
        """
        strategies = {
            'job_boards': {
                'dedup_method': 'strict_url',
                'content_check': False,
                'similarity_threshold': None
            },
            'news': {
                'dedup_method': 'content_similarity',
                'content_check': True,
                'similarity_threshold': 0.85
            },
            'social': {
                'dedup_method': 'mixed',
                'content_check': True,
                'similarity_threshold': 0.75
            }
        }
        return strategies.get(source_type, {})
```

## Quality Metrics

### 1. Signal Quality
Case-specific quality assessment:

```python
class SignalQualityMetrics:
    """
    Tracks signal quality metrics.
    
    Features:
    1. Case-specific benchmarking
    2. Historical comparison
    3. Enriched sampling
    
    Example:
        metrics = SignalQualityMetrics(case_type='warehouse_tech')
        quality = metrics.analyze_batch(signals)
    """
    
    def analyze_batch(self, 
                     signals: List[Dict[str, Any]],
                     enriched_sample: Optional[List] = None) -> Dict[str, float]:
        """
        Analyze signal batch quality.
        
        Process:
        1. Compare with similar cases
        2. Check historical performance
        3. Evaluate enriched samples
        
        Args:
            signals: Processed signals
            enriched_sample: Known good signals mixed in
        """
        return {
            'approval_rate': self._calc_approval_rate(signals),
            'historical_comparison': self._compare_historical(),
            'enriched_accuracy': self._check_enriched(enriched_sample)
        }
```

### 2. Prompt Performance
Evaluate prompt effectiveness:

```python
class PromptEvaluation:
    """
    Evaluates prompt performance using enriched samples.
    
    Method:
    1. Mix known signals (30% of batch)
    2. Run analysis
    3. Compare results
    
    Example:
        evaluator = PromptEvaluation(prompt_id='warehouse_v2')
        results = await evaluator.test_prompt()
    """
    
    async def test_prompt(self, 
                         sample_size: int = 30,
                         known_ratio: float = 0.3) -> Dict[str, float]:
        """
        Test prompt with enriched sample.
        
        Process:
        1. Prepare mixed sample
        2. Run analysis
        3. Calculate metrics
        
        Args:
            sample_size: Total sample size
            known_ratio: Ratio of known good signals
        """
        return {
            'detection_rate': self._calc_detection_rate(),
            'false_positive_rate': self._calc_false_positives(),
            'processing_efficiency': self._calc_efficiency()
        }
```

## Scalability Metrics

### 1. Parallel Processing
Measure parallel processing efficiency:

```python
parallel_metrics = {
    'collection': {
        'optimal_workers': 'workers at peak efficiency',
        'throughput': 'signals per minute',
        'resource_usage': 'CPU/memory per worker'
    },
    'analysis': {
        'batch_size': 'optimal items per batch',
        'concurrent_tasks': 'optimal concurrent analyses',
        'token_efficiency': 'tokens per signal'
    }
}
```

### 2. Case Comparison
Compare similar cases:

```python
class CaseComparison:
    """
    Compares performance across similar cases.
    
    Metrics:
    1. Signal yield (good signals per 1000)
    2. Processing efficiency
    3. Resource usage
    
    Example:
        comparison = CaseComparison(case_type='facility_signals')
        metrics = comparison.compare_cases(['warehouse', 'office'])
    """
    
    def normalize_metrics(self, 
                        case_metrics: Dict[str, float]) -> Dict[str, float]:
        """
        Normalize metrics for case comparison.
        
        Process:
        1. Adjust for case specifics
        2. Calculate relative performance
        3. Generate recommendations
        """
        return {
            'relative_yield': self._calc_relative_yield(),
            'efficiency_score': self._calc_efficiency_score(),
            'improvement_potential': self._calc_improvement()
        }
```

## Related Topics
- [Performance Optimization](optimization.md)
- [System Scaling](scaling.md)
- [Quality Control](../best-practices/quality-control.md)
- [Analysis Process](../business-processes/analysis-process.md) 