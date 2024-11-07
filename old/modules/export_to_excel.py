import sys
import os
import re

# Получаем путь к директории, содержащей текущий скрипт
current_dir = os.path.dirname(os.path.abspath(__file__))
# Получаем путь к корневой директории проекта (родительская директория для 'modules')
project_root = os.path.dirname(current_dir)
# Добавляем корневую директорию проекта в путь поиска модулей
sys.path.insert(0, project_root)
from urllib.parse import urlparse, parse_qs

import csv
import ast
from openpyxl import Workbook
from modules.link_finder import update_missing_links
from modules.link_utils import find_best_link

def clean_text(text):
    """Очищает текст от нежелательных символов."""
    return re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F-\x9F]', '', str(text))

def format_value(value):
    """Форматирует значение, делая первую букву заглавной."""
    if isinstance(value, str) and value:
        return value[0].upper() + value[1:].lower()
    return value

def truncate_text(text, max_length=10000):
    """Обрезает текст до заданной максимальной длины."""
    return text[:max_length] if len(text) > max_length else text

def clean_linkedin_link(link):
    """Очищает ссылку LinkedIn от дополнительных параметров."""
    if "linkedin.com" in link:
        return link.split('?')[0]
    return link

def safe_literal_eval(val):
    try:
        return ast.literal_eval(val)
    except (ValueError, SyntaxError):
        return val

def is_post_link(url):
    """Проверяет, является ли ссылка прямой ссылкой на пост в LinkedIn."""
    parsed_url = urlparse(url)
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
    for link in links:
        if is_post_link(link):
            return link
    return links[0] if links else "N/A"

def process_csv_to_excel(web_csv, li_csv, output_excel):
    print("Начало обработки CSV файлов")
    wb = Workbook()
    ws = wb.active
    ws.title = "Processed Data"

    headers = ["Mentioned Company", "Signal (True/False)", "Event Time", 
               "Source Link", "Text", "Author", "Title", "Source", "Summary"]
    ws.append(headers)

    data = []

    # Обработка веб-результатов
    if os.path.exists(web_csv):
        print(f"Обработка веб-результатов из файла: {web_csv}")
        with open(web_csv, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for i, row in enumerate(csv_reader):
                print(f"Обработка веб-строки {i+1}")
                analysis = safe_literal_eval(row['analysis'])
                
                if isinstance(analysis, list) and len(analysis) == 4:
                    company = clean_text(analysis[0])
                    signal = format_value(str(analysis[1]))
                    time = format_value(str(analysis[2]))
                    summary = clean_text(analysis[3])
                else:
                    company = "N/A"
                    signal = "N/A"
                    time = "N/A"
                    summary = "N/A"
                
                link = clean_text(row.get('link', 'N/A'))
                description = clean_text(row.get('description', 'N/A'))
                description = truncate_text(description, 10000)
                author = clean_text(row.get('author', 'N/A'))
                title = clean_text(row.get('title', 'N/A'))

                data.append({
                    'company': company,
                    'signal': signal,
                    'time': time,
                    'link': link,
                    'description': description,
                    'author': author,
                    'title': title,
                    'source': 'SERP',
                    'summary': summary
                })
    else:
        print(f"Файл веб-результатов не найден: {web_csv}")

    # Обработка LinkedIn-результатов
    if os.path.exists(li_csv):
        print(f"Обработка LinkedIn-результатов из файла: {li_csv}")
        with open(li_csv, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for i, row in enumerate(csv_reader):
                print(f"Обработка LinkedIn-строки {i+1}")
                analysis = safe_literal_eval(row['analysis'])
                
                if isinstance(analysis, list) and len(analysis) == 4:
                    company = clean_text(analysis[0])
                    signal = format_value(str(analysis[1]))
                    time = format_value(str(analysis[2]))
                    summary = clean_text(analysis[3])
                else:
                    company = "N/A"
                    signal = "N/A"
                    time = "N/A"
                    summary = "N/A"
                
                link = "N/A"  # Для LinkedIn-результатов ссылку нужно будет найти
                description = clean_text(row.get('description', 'N/A'))
                description = truncate_text(description, 10000)
                author = clean_text(row.get('title', 'N/A'))  # В LinkedIn автор записан в поле 'title'
                pubDate = row.get('pubDate', '')  # Добавляем дату публикации
                title = "N/A"  # У LinkedIn-постов нет заголовков

                data.append({
                    'company': company,
                    'signal': signal,
                    'time': time,
                    'link': link,
                    'description': description,
                    'author': author,
                    'pubDate': pubDate,  # Добавляем дату публикации
                    'title': title,
                    'source': 'LinkedIn',
                    'summary': summary
                })
    else:
        print(f"Файл LinkedIn-результатов не найден: {li_csv}")

    if not data:
        print("Ни один из входных файлов не был обработан. Выход из программы.")
        return

    print("Обновление отсутствующих ссылок")
    # data = update_missing_links(data)

    print("Запись данных в Excel файл")
    for item in data:
        ws.append([item['company'], item['signal'], item['time'], item['link'], 
                   item['description'], item['author'], item['title'], item['source'], item['summary']])

    wb.save(output_excel)
    print(f"Excel файл успешно создан: {output_excel}")

if __name__ == "__main__":
    web_csv = "results/farma/2024-07-33/search_results_analysed.csv"
    li_csv = "results/designers/2024-08-14/search_results_analysed.csv"
    output_excel = "output.xlsx"

    process_csv_to_excel(web_csv, li_csv, output_excel)