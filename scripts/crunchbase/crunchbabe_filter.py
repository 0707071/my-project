# Path: scripts/crunchbabe/crunchbabe_filter.py
# This script filters company data based on industry and location keywords from a configuration file,
# converts investment sizes into euros, and saves the result into a new Excel file.

import pandas as pd
import json
import requests

# Path to the input Excel file
excel_file_path = './scripts/crunchbabe/companies_data.xlsx'

# Function to fetch current exchange rates from an open API
def get_exchange_rates():
    url = "https://api.exchangerate-api.com/v4/latest/EUR"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['rates']
    else:
        raise Exception("Failed to fetch exchange rates")

# Function to convert currency values into euros, rounding to the nearest whole value
def convert_to_euro(value, currency, rates):
    if currency == '€':
        return round(value) if value else 'N/A'  # Already in euros, just round
    if currency == '$':
        return round(value / rates['USD']) if value else 'N/A'  # Convert USD to EUR
    if currency == '£':
        return round(value / rates['GBP']) if value else 'N/A'  # Convert GBP to EUR
    # Add other currencies as needed
    return 'N/A'  # Return 'N/A' for unknown or invalid values

# Main function to process the table
def process_table(excel_path, config_path):
    # Load the configuration file
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Load the Excel table
    df = pd.read_excel(excel_path)

    # Filter based on keywords
    industry_keywords = config['Industry']
    location_keywords = config['Location']

    # Filter rows based on Industry
    df_filtered = df[df['Industry'].str.contains('|'.join(industry_keywords), case=False, na=False)]

    # Filter rows based on Organization location
    df_filtered = df_filtered[df_filtered['Organization location'].str.contains('|'.join(location_keywords), case=False, na=False)]

    # Fetch exchange rates
    exchange_rates = get_exchange_rates()

    # Function to extract currency symbol from the Investment size column
    def extract_currency_symbol(value):
        if isinstance(value, str):
            for symbol in ['€', '$', '£']:
                if symbol in value:
                    return symbol
        return None

    # Function to extract numerical value from the Investment size column
    def extract_value(value):
        if isinstance(value, str):
            # Remove non-digit characters, hyphens, and spaces
            clean_value = ''.join(filter(str.isdigit, value.replace('-', '').replace(' ', '')))
            if clean_value:
                try:
                    return float(clean_value)
                except ValueError:
                    return None  # If conversion fails, return None
        elif isinstance(value, (int, float)):
            return value  # If already a number, return as is
        return None  # Return None for invalid values

    # Apply extraction functions to the relevant columns
    df_filtered['Currency'] = df_filtered['Investment size'].apply(extract_currency_symbol)
    df_filtered['Investment size'] = df_filtered['Investment size'].apply(extract_value)
    df_filtered['Amount in Euro'] = df_filtered.apply(
        lambda row: convert_to_euro(row['Investment size'], row['Currency'], exchange_rates), axis=1
    )

    # Fill any missing values in the 'Amount in Euro' column with 'N/A'
    df_filtered['Amount in Euro'].fillna('N/A', inplace=True)

    # Save the processed data to a new Excel file
    output_file = './scripts/crunchbabe/processed_companies_data.xlsx'
    df_filtered.to_excel(output_file, index=False)
    return output_file

# Path to the configuration file
config_file_path = './scripts/crunchbabe/config.json'

# Execute the processing
output_path = process_table(excel_file_path, config_file_path)

print(f"Processed data saved to: {output_path}")
