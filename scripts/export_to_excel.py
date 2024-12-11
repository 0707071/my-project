# Path: scripts/export_to_excel.py
# This script processes the 'analysis' column from a CSV file, splits it into multiple columns,
# and saves the result into an Excel file.

import pandas as pd
import ast
import re

def clean_analysis_string(analysis_str):
    """
    Cleans the analysis string by removing unwanted characters and returns the cleaned string.

    Args:
        analysis_str (str): The original analysis string from the CSV.

    Returns:
        str: Cleaned analysis string.
    """
    # Log the original string
    print(f"Original string: {analysis_str}")

    # Remove unwanted wrappers like "```python" and others
    cleaned_str = re.sub(r'```python|```', '', analysis_str).strip()  # Remove surrounding ```python``` blocks
    
    # Log the cleaned string
    print(f"Cleaned string: {cleaned_str}")
    return cleaned_str

def process_analysis(analysis_str):
    """
    Processes the analysis string, converting it into a list and splitting into individual columns.

    Args:
        analysis_str (str): The cleaned analysis string.

    Returns:
        tuple: A tuple of six elements (or fewer if the list has fewer items).
    """
    try:
        # Clean the string and convert it into a list
        cleaned_str = clean_analysis_string(analysis_str)
        
        # Attempt to convert the cleaned string to a list
        analysis_list = ast.literal_eval(cleaned_str)

        # Log the result of the conversion
        print(f"Converted list: {analysis_list}")

        # Function to clean elements inside the list
        def clean_element(element):
            if isinstance(element, list):
                return ', '.join(map(str, element)) if element else "N/A"
            return element

        # Process the list elements, handling nested lists and empty values
        analysis_list = [clean_element(item) for item in analysis_list]

        # Return the processed elements, ensuring a consistent output of 6 values
        if len(analysis_list) >= 6:
            return analysis_list[0], analysis_list[1], analysis_list[2], analysis_list[3], analysis_list[4], analysis_list[5]
        else:
            return analysis_list[0] if len(analysis_list) > 0 else "", \
                   analysis_list[1] if len(analysis_list) > 1 else "", \
                   analysis_list[2] if len(analysis_list) > 2 else "", \
                   analysis_list[3] if len(analysis_list) > 3 else "", \
                   analysis_list[4] if len(analysis_list) > 4 else "", \
                   analysis_list[5] if len(analysis_list) > 5 else ""
    except Exception as e:
        # Log any possible error and return empty values
        print(f"Error processing analysis: {str(e)}")
        return "", "", "", "", "", ""

# Read the CSV file
df = pd.read_csv('results/ALBI/2024-10-02/search_results_analysed.csv')

# Log the size of the DataFrame before processing
print(f"DataFrame size before processing: {df.shape}")

# Apply the process_analysis function to the 'analysis' column and split it into multiple columns
df[['Company', 'Signal', 'Time', 'Summary', 'Details1', 'Details2']] = df['analysis'].apply(process_analysis).apply(pd.Series)

# Log the result of the processing
print(df[['Company', 'Signal', 'Time', 'Summary', 'Details1', 'Details2']].head())

# Save the result to an Excel file
df.to_excel('results/ALBI/2024-10-02/ALBI_2024-10-02.xlsx', index=False)

print("Processing completed. The result is saved to 'results/ALBI/2024-10-02/ALBI_2024-10-02.xlsx'.")
