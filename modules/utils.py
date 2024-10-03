# Path: modules/utils.py
# Utility file with various helper functions used across different modules.
# It includes configuration loading, API request handling, and text processing functions.

import os
import sys
import re
import json
import time
import asyncio
import aiohttp
from itertools import cycle
from functools import wraps
import google.generativeai as genai

# Load configuration
try:
    with open('config/search_config.json', 'r') as f:
        config = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    print("Error reading configuration file. Using default values.")
    config = {}

# Load API keys
try:
    from config.api_keys import api_keys
except ImportError:
    print("Error importing api_keys. Make sure the file exists and contains the required keys.")
    api_keys = {}

# Gemini API settings
use_gemini = config.get("use_gemini", True)
gemini_rate_limit = config.get("gemini_rate_limit", 20)  # Requests per minute
gemini_api_keys = api_keys.get("gemini_api_keys", [])

if not gemini_api_keys:
    print("Warning: The Gemini API keys list is empty. Make sure keys are properly set in api_keys.py")

gemini_key_cycle = cycle(gemini_api_keys)


def clean_domain(domain):
    """
    Cleans up the domain name by removing prefixes like http, https, www.
    
    Args:
        domain (str): The original domain.
    
    Returns:
        str: Cleaned domain name.
    """
    domain = domain.lower()
    domain = re.sub(r'^https?://', '', domain)
    domain = re.sub(r'^www\.', '', domain)
    return domain.split('/')[0]


async def rate_limited_request(session, url, payload, api_key):
    """
    Performs an HTTP POST request with rate limiting and API key authorization.
    
    Args:
        session (aiohttp.ClientSession): The aiohttp session for making requests.
        url (str): The target URL.
        payload (dict): The payload to send in the POST request.
        api_key (str): The API key for authorization.
    
    Returns:
        dict: The JSON response from the request.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    async with session.post(url, json=payload, headers=headers) as response:
        return await response.json()


async def gpt_query_async(messages, timeout=120, max_retries=3):
    """
    Sends an asynchronous request to the Gemini API for GPT query.
    
    Args:
        messages (list): List of message dicts for the GPT query.
        timeout (int, optional): Maximum time in seconds to wait for the response. Default is 120.
        max_retries (int, optional): Maximum number of retries in case of failure. Default is 3.
    
    Returns:
        tuple: A tuple containing the response content and number of tokens used.
    """
    if use_gemini:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={next(gemini_key_cycle)}"
        payload = {
            "contents": [{"parts": [{"text": msg['content']} for msg in messages]}]
        }

        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    response = await asyncio.wait_for(
                        session.post(url, json=payload),
                        timeout=timeout
                    )
                    response_json = await response.json()

                    if 'error' in response_json:
                        error_message = response_json['error'].get('message', 'Unknown error')
                        print(f"Gemini API error (attempt {attempt + 1}): {error_message}")
                        
                        if "Resource has been exhausted" in error_message:
                            if attempt < max_retries - 1:
                                print("Waiting 60 seconds before retrying...")
                                await asyncio.sleep(60)
                                continue

                        if attempt == max_retries - 1:
                            return f"API Error: {error_message}", 0
                        continue

                    if 'candidates' not in response_json:
                        print(f"Unexpected response format from Gemini API: {response_json}")
                        if attempt == max_retries - 1:
                            return "Unexpected response format from API", 0
                        continue

                    content = response_json['candidates'][0]['content']['parts'][0]['text']
                    tokens_used = len(' '.join(msg['content'] for msg in messages).split()) + len(content.split())
                    return content, tokens_used

            except asyncio.TimeoutError:
                print(f"Timeout: Request took longer than {timeout} seconds.")
                if attempt == max_retries - 1:
                    return "timeout", 0
            except Exception as e:
                print(f"Error in Gemini API request: {e}")
                if attempt == max_retries - 1:
                    return str(e), 0

            # Wait before the next retry
            if attempt < max_retries - 1:
                await asyncio.sleep(5)
    else:
        # Placeholder for OpenAI GPT-4 asynchronous version
        print("Asynchronous version for OpenAI GPT-4 not implemented")
        return "Not implemented", 0


def load_role_description(file_path):
    """
    Loads and returns the content of a file containing a role description.
    
    Args:
        file_path (str): The path to the file.
    
    Returns:
        str: The role description content.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read().strip()


def signal_handler(sig, frame, workbook, filename, verbose=False):
    """
    Handles signals like Ctrl+C, saves and closes the workbook before exiting.
    
    Args:
        sig (int): Signal number.
        frame: Current stack frame.
        workbook (Workbook): Open workbook object.
        filename (str): The filename where the workbook will be saved.
        verbose (bool, optional): Whether to print detailed output. Default is False.
    """
    if verbose:
        print('You pressed Ctrl+C! Saving and closing the file...')
    workbook.save(filename)
    workbook.close()
    sys.exit(0)


def save_results_to_csv(results, output_filename, verbose=False):
    """
    Saves the results to a CSV file.
    
    Args:
        results (list): List of results to be saved.
        output_filename (str): Path to the output CSV file.
        verbose (bool, optional): Whether to print detailed output. Default is False.
    """
    df = pd.DataFrame(results)
    df.to_csv(output_filename, index=False)
    if verbose:
        print(f"Results successfully saved to file: {output_filename}")


def clean_text(text):
    """
    Cleans the text by removing unwanted characters.
    
    Args:
        text (str): The input text.
    
    Returns:
        str: Cleaned text.
    """
    return re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F-\x9F]', '', str(text))


def format_value(value):
    """
    Formats a value by capitalizing the first letter.
    
    Args:
        value (str): The input string value.
    
    Returns:
        str: Formatted string with the first letter capitalized.
    """
    if isinstance(value, str) and value:
        return value[0].upper() + value[1:].lower()
    return value


def truncate_text(text, max_length=10000):
    """
    Truncates the text to a specified maximum length.
    
    Args:
        text (str): The input text.
        max_length (int, optional): The maximum allowed length. Default is 10,000 characters.
    
    Returns:
        str: Truncated text.
    """
    return text[:max_length] if len(text) > max_length else text


def clean_linkedin_link(link):
    """
    Cleans a LinkedIn URL by removing unnecessary parameters.
    
    Args:
        link (str): The original LinkedIn URL.
    
    Returns:
        str: Cleaned LinkedIn URL.
    """
    if "linkedin.com" in link:
        return link.split('?')[0]
    return link


def load_config(config_file):
    """
    Loads configuration from a JSON file.
    
    Args:
        config_file (str): Path to the configuration file.
    
    Returns:
        dict: Loaded configuration as a dictionary.
    """
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Configuration file not found: {config_file}")
        return {}
    except json.JSONDecodeError:
        print(f"Error reading configuration file: {config_file}")
        return {}
