import asyncio
import sys
sys.path.append('.')  # Add current directory to path
from modules.fetch_data import fetch_xmlstock_search_results

async def test_query_generation():
    
    """
    Generates search queries by combining each keyword phrase with each include word 
    and appending exclude words. The queries are printed in a numbered list, along 
    with a summary of the input counts.

    Example:
    For keywords: "arduino", "mid-sized logistics company", "freight carrier",
    include words: "nginx", "pharma", "vaccines", "cold chain logistics", 
    and exclude words: "-third-party", "-wholesale", the function generates queries 
    like:
    - "arduino 'nginx' -third-party -wholesale"
    - "mid-sized logistics company 'nginx' -third-party -wholesale"

    Returns:
        list: A list of generated queries.
    """

    # Mock config
    config = {'results_per_page': 10, 'days': 7, 'num_pages': 1}
    
    # Test case from requirements
    keywords = 'arduino\n"mid-sized logistics company"\n"freight carrier"'
    include_words = 'nginx\npharma\nvaccines\ncold chain logistics'
    exclude_words = '-third-party -wholesale'
    
    # Create a wrapper to avoid API calls
    async def test_wrapper():
        # Generate queries as normal
        keyword_phrases = [kw.strip() for kw in keywords.split('\n') if kw.strip()]
        include_phrases = [inc.strip() for inc in include_words.split('\n') if inc.strip()] if include_words else []
        
        if not include_phrases:
            include_phrases = ['']
        
        exclude_str = f' {exclude_words}' if exclude_words else ''
        
        all_queries = []
        for keyword in keyword_phrases:
            for include_word in include_phrases:
                if include_word:
                    full_query = f'{keyword} "{include_word}"{exclude_str}'
                else:
                    full_query = f'{keyword}{exclude_str}'
                all_queries.append(full_query)
        
        print(f'Generated {len(all_queries)} queries using multiplication approach:')
        for idx, q in enumerate(all_queries, 1):
            print(f'{idx}. {q}')
        
        return all_queries
    
    # Run the test
    queries = await test_wrapper()
    
    # Print summary

    num_keywords = len(keywords.split("\n"))
    num_include_words = len(include_words.split("\n"))

    print(f'- {num_keywords} keyword phrases')
    print(f'- {num_include_words} include words')
# Run the test
if __name__ == "__main__":
    asyncio.run(test_query_generation())
