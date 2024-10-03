# Path: scripts/crunchbase/crunchbase.py
# This script converts company data from a text file to an Excel table.

import pandas as pd
import re

def parse_company_data(file_path):
    """
    Parses the input text file containing company data.
    
    Args:
        file_path (str): Path to the input text file.

    Returns:
        list: List of dictionaries where each dictionary represents a company.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Split companies by empty lines
    companies = re.split(r'\n\s*\n', content.strip())
    
    data = []
    for company in companies:
        company_data = company.split('\n')
        row = {}
        for field in company_data:
            if ' - ' in field:
                continue  # Skip lines with logos or unnecessary content
            if ':' in field:
                key, value = field.split(':', 1)
                row[key.strip()] = value.strip()
            else:
                row[len(row)] = field.strip()  # Add fields without keys by index
        data.append(row)

    return data

def create_excel(data, output_file):
    """
    Creates an Excel file from the parsed company data.
    
    Args:
        data (list): List of dictionaries with company data.
        output_file (str): Path to the output Excel file.
    """
    # Define the desired columns in the final Excel file
    columns = [
        'Transaction name',
        'Organization name',
        'Founding type',
        'Investment size',
        'Investment date',
        'Founding stage',
        'Organization description',
        'Industry',
        'Website',
        'Organization location',
        'Total funding amount',
        'Founding status',
        'Number of founders',
        'Investor names',
        'Lead investors',
        'Number of investors'
    ]

    df = pd.DataFrame(data)
    
    # Rename columns according to the specified order
    df = df.rename(columns={
        0: 'Transaction name',
        1: 'Organization name',
        2: 'Founding type',
        3: 'Investment size',
        4: 'Investment date',
        5: 'Founding stage',
        6: 'Organization description',
        7: 'Industry',
        8: 'Website',
        9: 'Organization location',
        10: 'Total funding amount',
        11: 'Founding status',
        12: 'Number of founders',
        13: 'Investor names',
        14: 'Lead investors',
        15: 'Number of investors'
    })
    
    # Select only the required columns in the specified order
    df = df[columns]

    # Save to Excel
    df.to_excel(output_file, index=False, engine='openpyxl')

if __name__ == "__main__":
    # Specify the input text file path and the output Excel file path
    input_file = "scripts/crunchbase/companies.txt"  # Path to your input text file
    output_file = "scripts/crunchbase/companies_data.xlsx"  # Desired name for the output Excel file

    # Parse the company data from the input file
    data = parse_company_data(input_file)

    # Create the Excel file from the parsed data
    create_excel(data, output_file)
    print(f"Data successfully saved to file {output_file}")
