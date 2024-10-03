# Path: modules/clean_data.py
# This file is responsible for cleaning the data by removing strict and non-strict duplicates.

import pandas as pd
from fuzzywuzzy import fuzz


def clean_data(input_filename, output_filename, similarity_threshold=80, verbose=False):
    """
    Clean data by removing strict and non-strict duplicates.

    Args:
        input_filename (str): Path to the input CSV file.
        output_filename (str): Path to the output CSV file.
        similarity_threshold (int): Similarity threshold for fuzzy matching (default is 80).
        verbose (bool): Flag to enable/disable verbose output.

    Returns:
        tuple: Number of rows before and after cleaning.
    """
    print("Starting clean_data function")
    print(f"Loading data from file {input_filename}...")

    # Try to load the input file into a DataFrame
    try:
        df = pd.read_csv(input_filename)
        print(f"Data successfully loaded. Number of rows: {len(df)}")
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        raise

    rows_before = len(df)

    # Stage 1: "Strict" comparison and removal of exact duplicates
    print("Removing strict duplicates...")
    df_no_strict_duplicates = df.drop_duplicates(subset=['title', 'description']).reset_index(drop=True)
    print(f"Strict duplicates removed: {len(df) - len(df_no_strict_duplicates)}")

    # Stage 2: Preparation for "non-strict" comparison using fuzzy matching
    print("Preparing data for 'non-strict' comparison...")
    df_no_strict_duplicates_sorted = df_no_strict_duplicates.sort_values('title').reset_index()

    # List of row indices to remove
    indexes_to_remove = set()

    print("Searching for duplicates with 'non-strict' comparison...")
    # Using fuzzy matching to find similar duplicates based on title and description
    for i in range(len(df_no_strict_duplicates_sorted) - 1):
        for j in range(i + 1, len(df_no_strict_duplicates_sorted)):
            # Use fuzz.token_sort_ratio to compare strings
            similarity_title = fuzz.token_sort_ratio(
                df_no_strict_duplicates_sorted.loc[i, 'title'], df_no_strict_duplicates_sorted.loc[j, 'title'])
            similarity_text = fuzz.token_sort_ratio(
                df_no_strict_duplicates_sorted.loc[i, 'description'], df_no_strict_duplicates_sorted.loc[j, 'description'])

            # If similarity of descriptions exceeds the threshold, mark as a duplicate
            if similarity_text > similarity_threshold:
                indexes_to_remove.add(df_no_strict_duplicates_sorted.loc[j, 'index'])  # Mark index for removal
                if verbose:
                    print(f"Duplicate found: row {i + 1} and row {j + 1}")
                    print(f"Title similarity: {similarity_title}, Text similarity: {similarity_text}")

    # Remove duplicates found in the 'non-strict' comparison stage
    df_final = df_no_strict_duplicates_sorted.drop(
        df_no_strict_duplicates_sorted[df_no_strict_duplicates_sorted['index'].isin(indexes_to_remove)].index).reset_index(drop=True)

    print("Saving cleaned data...")
    # Save the cleaned data to a new CSV file
    df_final.to_csv(output_filename, index=False)

    rows_after = len(df_final)

    # Output information about the number of removed and remaining rows
    print(f"Rows removed during 'non-strict' comparison: {len(indexes_to_remove)}")
    print(f"Remaining rows after cleaning: {rows_after}")
    print(f"Data cleaned and saved to '{output_filename}'.")

    print("End of clean_data function")
    return rows_before, rows_after
