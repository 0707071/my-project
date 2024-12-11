# Data Handling
# Data Handling

## Input Validation

### 1. Data Validation Patterns
Best practices for validating input data:

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict

@dataclass
class SearchInput:
    """
    Structured input data for search operations.
    
    This class demonstrates:
    1. Strong typing for input validation
    2. Default values for optional fields
    3. Built-in validation methods
    4. Clear documentation of requirements
    
    Example usage:
        search_input = SearchInput(
            query="company expansion news",
            date_range=30,
            sources=["news", "press-releases"]
        )
        if search_input.validate():
            results = await process_search(search_input)
    """
    query: str
    date_range: int
    sources: List[str]
    min_confidence: float = 0.7
    max_results: Optional[int] = None
    metadata: Dict[str, Any] = None
    
    def validate(self) -> bool:
        """
        Validate search input parameters.
        
        Validation rules:
        1. Query length between 2 and 500 chars
        2. Date range between 1 and 365 days
        3. At least one valid source
        4. Confidence threshold between 0 and 1
        """
        try:
            # Query validation
            if not (2 <= len(self.query.strip()) <= 500):
                raise ValueError("Query must be between 2 and 500 characters")
                
            # Date range validation
            if not (1 <= self.date_range <= 365):
                raise ValueError("Date range must be between 1 and 365 days")
                
            # Sources validation
            if not self.sources:
                raise ValueError("At least one source must be specified")
                
            # Confidence threshold validation
            if not (0 <= self.min_confidence <= 1):
                raise ValueError("Confidence threshold must be between 0 and 1")
                
            return True
            
        except Exception as e:
            logging.error(f"Validation error: {str(e)}")
            return False
```

### 2. Data Cleaning Strategies
Implementing robust data cleaning:

```python
class DataCleaner:
    """
    Handles data cleaning and normalization.
    
    Features:
    1. HTML stripping with tag preservation
    2. Text normalization
    3. Intelligent duplicate detection
    4. Special character handling
    5. Date format standardization
    
    Example usage:
        cleaner = DataCleaner(config={
            'allowed_tags': ['p', 'a', 'b'],
            'text_length_limits': {'max': 10000}
        })
        cleaned_text = cleaner.clean_text(raw_html)
    """
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Process:
        1. Remove HTML (preserving allowed tags)
        2. Normalize whitespace
        3. Handle special characters
        4. Apply length limits
        
        Example:
            >>> cleaner.clean_text("<p>Company <b>expansion</b> news</p>")
            "Company expansion news"
        """
        # Step 1: Basic cleaning
        cleaned = self.text_processor.strip_html(text)
        
        # Step 2: Normalize whitespace
        cleaned = ' '.join(cleaned.split())
        
        # Step 3: Handle special characters
        cleaned = self.text_processor.normalize_chars(cleaned)
        
        # Step 4: Apply length limits
        if len(cleaned) > self.config['text_length_limits']['max']:
            cleaned = cleaned[:self.config['text_length_limits']['max']]
            
        return cleaned.strip()
        
    def is_duplicate(self, text1: str, text2: str) -> bool:
        """
        Check if two texts are duplicates using multiple methods.
        
        Methods:
        1. Levenshtein distance for similarity
        2. Semantic similarity check
        3. URL pattern matching
        4. Content fingerprinting
        
        Example:
            >>> is_dup = cleaner.is_duplicate(text1, text2)
            >>> print(f"Duplicate detected: {is_dup}")
        """
        # Calculate similarity scores
        leven_ratio = levenshtein_ratio(text1, text2)
        semantic_sim = semantic_similarity(text1, text2)
        
        # Check URL patterns
        urls1 = extract_urls(text1)
        urls2 = extract_urls(text2)
        url_match = bool(set(urls1) & set(urls2))
        
        # Combined decision
        return (
            leven_ratio > self.config['similarity_threshold'] or
            semantic_sim > self.config['similarity_threshold'] or
            url_match
        )
```

## Data Storage

### 1. Database Operations
Implementing safe and efficient database operations:

```python
class DataManager:
    """
    Manages database operations with safety and efficiency.
    
    Features:
    1. Connection pooling
    2. Transaction management
    3. Error handling with retries
    4. Query optimization
    5. Data integrity checks
    
    Example usage:
        manager = DataManager(db_config)
        await manager.store_results(processed_data)
    """
    
    async def store_results(self, 
                          results: List[Dict[str, Any]],
                          batch_size: int = 100) -> None:
        """
        Store analysis results in database with batching.
        
        Features:
        1. Batch processing for efficiency
        2. Transaction management
        3. Error handling with rollback
        4. Duplicate checking
        
        Example:
            >>> results = [{"id": 1, "data": "..."}, ...]
            >>> await manager.store_results(results)
        """
        async with self.engine.begin() as conn:
            try:
                for i in range(0, len(results), batch_size):
                    batch = results[i:i + batch_size]
                    
                    # Check for duplicates
                    unique_batch = await self._filter_duplicates(batch)
                    
                    # Prepare batch insert
                    stmt = insert(SearchResult).values(unique_batch)
                    
                    # Execute with conflict handling
                    await conn.execute(
                        stmt.on_conflict_do_nothing(
                            index_elements=['url']
                        )
                    )
                    
            except Exception as e:
                logging.error(f"Database error: {str(e)}")
                raise DatabaseError(f"Failed to store results: {str(e)}")
```

