import aiohttp
from bs4 import BeautifulSoup
import logging

async def fetch_and_clean_website_content(url: str, max_length: int = 5000) -> str:
    """
    Асинхронно получает содержимое веб-страницы и очищает его от HTML-разметки.
    
    :param url: URL веб-страницы
    :param max_length: Максимальная длина возвращаемого текста
    :return: Очищенный текст веб-страницы
    """
    if not url or not isinstance(url, str):
        return "Error: Invalid URL"

    # Добавляем протокол, если его нет
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Удаляем все скрипты и стили
                    for script_or_style in soup(["script", "style"]):
                        script_or_style.decompose()
                    
                    # Получаем текст
                    text = soup.get_text(separator=' ', strip=True)
                    
                    # Ограничиваем длину текста
                    return text[:max_length]
                else:
                    return f"Error: Unable to fetch content (status {response.status})"
    except Exception as e:
        logging.error(f"Ошибка при получении содержимого сайта {url}: {str(e)}")
        return f"Error: {str(e)}"
