from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup

def is_linkedin_post_link(url):
    """Проверяет, является ли ссылка прямой ссылкой на пост в LinkedIn."""
    parsed_url = urlparse(url)
    if "linkedin.com" not in parsed_url.netloc:
        return False
    
    path_parts = parsed_url.path.split('/')
    
    # Проверяем, что URL содержит '/posts/' или '/pulse/'
    if '/posts/' in parsed_url.path or '/pulse/' in parsed_url.path:
        return True
    
    # Проверяем наличие идентификатора активности
    query_params = parse_qs(parsed_url.query)
    if 'activityId' in query_params:
        return True
    
    return False

def find_best_link(links):
    """Выбирает лучшую ссылку из списка найденных."""
    linkedin_links = [link for link in links if is_linkedin_post_link(link)]
    
    if linkedin_links:
        return linkedin_links[0]
    elif links:
        return links[0]
    else:
        return "N/A"

def validate_linkedin_link(url: str, original_text: str, max_chars: int = 100) -> bool:
    """
    Проверяет, соответствует ли контент по ссылке исходному тексту поста.
    
    Args:
    url (str): URL для проверки
    original_text (str): Исходный текст поста
    max_chars (int): Максимальное количество символов для сравнения

    Returns:
    bool: True, если контент соответствует, иначе False
    """
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return False
        
        soup = BeautifulSoup(response.text, 'html.parser')
        post_content = soup.find('div', class_='feed-shared-update-v2__description')
        
        if not post_content:
            return False
        
        post_text = post_content.get_text(strip=True)
        
        # Сравниваем первые max_chars символов
        return original_text[:max_chars].lower() in post_text.lower()
    except Exception as e:
        print(f"Ошибка при валидации ссылки: {e}")
        return False