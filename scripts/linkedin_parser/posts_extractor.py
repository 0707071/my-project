# Path: scripts/linkedin_parser/posts_extractor.py
# This script parses LinkedIn HTML files to extract post information and saves the results into a CSV file.

import os
import csv
from bs4 import BeautifulSoup
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_html_file(file_path):
    """
    Parses an HTML file to extract LinkedIn post data.

    Args:
        file_path (str): Path to the HTML file.

    Returns:
        list: A list of dictionaries containing post information.
    """
    logging.info(f"Parsing file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
            posts = []

            # Extract query from the file name
            file_name = os.path.basename(file_path)
            query_match = re.search(r'(.+?) \* Поиск \* LinkedIn\.html', file_name)
            query = query_match.group(1) if query_match else ""

            # Find all posts in the HTML file
            all_posts = soup.find_all('div', class_='feed-shared-update-v2')
            logging.info(f"Found posts: {len(all_posts)}")

            for post in all_posts:
                try:
                    # Extract post text (description)
                    text_element = post.find('span', class_='break-words')
                    description = ' '.join(text_element.stripped_strings) if text_element else ''
                    logging.info(f"Post text: {description[:50]}...")  # Log first 50 characters

                    # Extract author information (title) and link to the author (link)
                    author_element = post.find('a', class_='app-aware-link update-components-actor__meta-link')
                    if author_element:
                        title = author_element.find('span', class_='update-components-actor__name').get_text(strip=True)
                        link = author_element.get('href', '')
                        logging.info(f"Author (title): {title}")
                        logging.info(f"Author link (link): {link}")
                    else:
                        title = ''
                        link = ''
                        logging.warning("Author information not found")

                    # Add pubDate (empty value, as it's not available in the source data)
                    pubDate = ''

                    # Append the post data to the list
                    posts.append({
                        'title': title,
                        'link': link,
                        'pubDate': pubDate,
                        'description': description,
                        'query': query
                    })

                except Exception as e:
                    logging.error(f"Error processing post: {str(e)}")

            return posts
    except Exception as e:
        logging.error(f"Error opening or parsing file {file_path}: {str(e)}")
        return []

def main():
    # Define the folder with HTML files relative to the script
    html_folder = './HTML'
    output_file = 'search_results.csv'

    all_posts = []

    # Iterate over all HTML files in the folder
    for filename in os.listdir(html_folder):
        if filename.endswith('.html'):
            file_path = os.path.join(html_folder, filename)
            file_posts = parse_html_file(file_path)
            all_posts.extend(file_posts)
            logging.info(f"Processed posts in file {filename}: {len(file_posts)}")

    logging.info(f"Total posts processed: {len(all_posts)}")

    # Write the results to a CSV file
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['title', 'link', 'pubDate', 'description', 'query']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for post in all_posts:
            writer.writerow(post)

    logging.info(f"Parsing completed. Results saved to {output_file}")

if __name__ == "__main__":
    main()
