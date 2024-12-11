# Client Workflow

## Overview

The client workflow consists of two main configuration components:
- Search queries for data collection
- Analysis prompts for signal detection

Each component can be saved as a preset and combined flexibly for different analysis tasks.

## Workflow Stages
Client Process Flow:
```text

Initial Setup -> Search Config -> Data Collection -> Signal Analysis -> Manual Review -> Client Delivery
                             -> Prompt Design                      -> System Updates -> Back to Config
```

## Configuration Process

### 1. Search Setup
Create and manage search queries:

```python
class SearchConfiguration:
    """
    Manages search query configurations.
    
    Features:
    1. Query management
    2. Source selection
    3. Performance tracking
    4. Notes and metadata
    
    Example usage:
        config = SearchConfiguration(client_id='client123')
        await config.save_preset('warehouse_tech')
    """
    
    def save_preset(self, name: str, notes: str = "") -> Dict[str, Any]:
        """
        Save search configuration as preset.
        
        Stores:
        - Query patterns
        - Source settings
        - Performance metrics
        - Analyst notes
        """
        return {
            'name': name,
            'queries': self.queries,
            'sources': self.sources,
            'metrics': self._get_metrics(),
            'notes': notes,
            'created_at': datetime.utcnow()
        }
```

### 2. Prompt Engineering
Design and optimize analysis prompts:

```python
class PromptConfiguration:
    """
    Manages analysis prompt configurations.
    
    Features:
    1. Prompt templates
    2. Output columns
    3. Example management
    4. Performance tracking
    
    Example usage:
        config = PromptConfiguration(industry='warehouse_tech')
        await config.save_preset('motion_sensors')
    """
    
    def save_preset(self, name: str, notes: str = "") -> Dict[str, Any]:
        """
        Save prompt configuration as preset.
        
        Stores:
        - Prompt template
        - Output format
        - Example cases
        - Performance data
        - Analyst notes
        """
        return {
            'name': name,
            'template': self.template,
            'output_columns': self.columns,
            'examples': self.examples,
            'metrics': self._get_metrics(),
            'notes': notes,
            'created_at': datetime.utcnow()
        }
```

## Analysis Workflow

### 1. Task Execution
Combine search and analysis configurations:

```python
class AnalysisTask:
    """
    Manages analysis task execution.
    
    Process:
    1. Load configurations
    2. Execute search
    3. Apply analysis
    4. Filter results
    
    Example usage:
        task = AnalysisTask(
            search_preset='warehouse_tech',
            prompt_preset='motion_sensors'
        )
        results = await task.execute()
    """
    
    async def execute(self) -> Dict[str, Any]:
        """
        Execute analysis task.
        
        Steps:
        1. Validate configurations
        2. Collect raw data
        3. Process signals
        4. Apply filters
        5. Generate report
        """
        return {
            'raw_count': self.total_results,
            'processed_count': self.processed_results,
            'filtered_count': self.filtered_results,
            'top_signals': self.top_signals,
            'metrics': self.execution_metrics
        }
```

### 2. Result Review
Manual validation and scoring:

```python
class ResultReview:
    """
    Manages manual result review process.
    
    Features:
    1. Signal scoring (1-5)
    2. Error pattern detection
    3. Improvement suggestions
    4. Performance tracking
    
    Example usage:
        review = ResultReview(task_id='task123')
        await review.complete_review()
    """
    
    async def complete_review(self) -> Dict[str, Any]:
        """
        Complete manual review process.
        
        Process:
        1. Score signals
        2. Identify patterns
        3. Generate insights
        4. Update metrics
        """
        return {
            'reviewed_count': self.reviewed_signals,
            'selected_count': self.selected_signals,
            'error_patterns': self.identified_patterns,
            'suggestions': self.improvement_suggestions
        }
```

## System Improvement

### 1. Performance Analysis
Track and analyze system performance:

```python
performance_metrics = {
    'search_efficiency': {
        'query_performance': {},  # Query-specific metrics
        'source_quality': {},     # Source-specific metrics
        'coverage_analysis': {}   # Coverage statistics
    },
    'analysis_quality': {
        'prompt_effectiveness': {},  # Prompt-specific metrics
        'signal_accuracy': {},       # Signal quality metrics
        'processing_efficiency': {}  # Processing statistics
    }
}
```

### 2. Continuous Improvement
Iterative system optimization:

```python
improvement_workflow = {
    'search_optimization': [
        'Remove ineffective queries',
        'Expand successful patterns',
        'Adjust source weights',
        'Update filtering rules'
    ],
    'prompt_optimization': [
        'Refine signal definitions',
        'Update example cases',
        'Adjust scoring criteria',
        'Enhance output format'
    ]
}
```

## Analyst Workflow

### Initial Client Setup

1. **Client Requirements Analysis**
   ```python
   client_profile = {
       'industry': 'warehouse_technology',
       'target_markets': ['Nordics', 'Baltics'],
       'company_size': {
           'min_revenue': 'up to 100M',
           'max_revenue': 'up to 5000M'
       },
       'special_focus': [
           'cold storage facilities',
           'logistics centers',
           'manufacturing plants'
       ]
   }
   ```

2. **Search Strategy Development**
   ```python
   search_strategy = {
       'primary_sources': [
           'industry_news',
           'company_announcements',
           'construction_permits'
       ],
       'signal_types': [
           'expansion_plans',
           'facility_upgrades',
           'energy_efficiency_initiatives'
       ],
       'update_frequency': '12h'
   }
   ```

### Iterative Optimization

1. **Signal Quality Assessment**
   ```python
   class SignalQualityAnalysis:
       """
       Analyzes signal quality and suggests improvements.
       
       Process:
       1. Review top/bottom signals
       2. Identify patterns in false positives
       3. Document successful patterns
       4. Update configurations
       
       Note: Document insights in notes field for future reference
       """
       
       def analyze_batch(self, 
                        signals: List[Dict[str, Any]],
                        analyst_scores: Dict[int, int]) -> Dict[str, Any]:
           """
           Analyze batch of signals with analyst scores.
           
           Args:
               signals: List of processed signals
               analyst_scores: Manual scores (1-5) for signals
               
           Returns:
               Analysis results and improvement suggestions
           """
           return {
               'high_quality_patterns': self._analyze_top_signals(signals, analyst_scores),
               'noise_patterns': self._analyze_low_quality(signals, analyst_scores),
               'suggested_updates': self._generate_suggestions(),
               'effectiveness_metrics': self._calculate_metrics()
           }
   ```

2. **Configuration Refinement**
   ```python
   class ConfigurationOptimizer:
       """
       Optimizes search and prompt configurations based on results.
       
       Key aspects:
       1. Query effectiveness tracking
       2. Source quality monitoring
       3. Prompt performance analysis
       4. Cost-benefit analysis
       
       Example:
           optimizer = ConfigurationOptimizer(client_id='client123')
           suggestions = await optimizer.analyze_performance()
       """
       
       async def analyze_performance(self) -> Dict[str, Any]:
           """
           Analyze configuration performance.
           
           Analysis includes:
           - Query hit rates
           - Source value metrics
           - Processing efficiency
           - Signal quality distribution
           """
           return {
               'query_metrics': self._analyze_queries(),
               'source_metrics': self._analyze_sources(),
               'prompt_metrics': self._analyze_prompts(),
               'optimization_suggestions': self._generate_suggestions()
           }
   ```

### Quality Control Process

1. **Manual Review Guidelines**
   ```python
   review_guidelines = {
       'signal_scoring': {
           5: 'Perfect match, ready for client',
           4: 'Good signal, needs minor refinement',
           3: 'Potential signal, needs investigation',
           2: 'Weak signal, likely noise',
           1: 'Complete miss, update filters'
       },
       'review_steps': [
           'Verify company details',
           'Validate signal relevance',
           'Check revenue range',
           'Assess timing/urgency',
           'Evaluate action potential'
       ],
       'documentation': {
           'required_notes': [
               'Quality issues found',
               'Improvement suggestions',
               'Pattern observations'
           ]
       }
   }
   ```

2. **Continuous Learning**
   ```python
   class LearningSystem:
       """
       Manages system learning from analyst feedback.
       
       Features:
       1. Pattern recognition
       2. Error analysis
       3. Configuration updates
       4. Performance tracking
       
       Note: Document all insights for team knowledge sharing
       """
       
       async def process_feedback(self,
                                batch_results: Dict[str, Any],
                                analyst_feedback: Dict[str, Any]) -> Dict[str, Any]:
           """
           Process analyst feedback and update system.
           
           Steps:
           1. Analyze feedback patterns
           2. Update configurations
           3. Track improvements
           4. Generate reports
           """
           return {
               'identified_patterns': self._analyze_patterns(),
               'suggested_updates': self._generate_updates(),
               'performance_impact': self._estimate_impact(),
               'learning_summary': self._generate_summary()
           }
   ```

### Client Delivery

1. **Result Selection**
   ```python
   class ResultSelector:
       """
       Manages final result selection for client delivery.
       
       Process:
       1. Filter by score (typically 4-5)
       2. Remove duplicates
       3. Group by signal type
       4. Sort by relevance
       
       Example:
           selector = ResultSelector(min_score=4)
           delivery = await selector.prepare_delivery()
       """
       
       async def prepare_delivery(self) -> Dict[str, Any]:
           """
           Prepare results for client delivery.
           
           Steps:
           1. Apply selection criteria
           2. Format results
           3. Generate insights
           4. Create summary
           """
           return {
               'selected_signals': self._select_signals(),
               'signal_groups': self._group_signals(),
               'key_insights': self._generate_insights(),
               'delivery_summary': self._create_summary()
           }
   ```

## Related Topics
- [Search Configuration](search-config.md)
- [Analysis Process](analysis-process.md)
- [Quality Metrics](../performance/metrics.md)
- [Best Practices](../best-practices/index.md)
- [Quality Control](../best-practices/quality-control.md)
- [Analyst Guidelines](../guides/analyst-workflow.md) 