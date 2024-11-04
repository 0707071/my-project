from app import db
from datetime import datetime
from app.models.prompt import PromptField
import json
import re

class SearchResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('search_task.id'), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(500))
    snippet = db.Column(db.Text)
    content = db.Column(db.Text)
    analysis = db.Column(db.Text)  # Сырой ответ LLM в формате Python list
    published_date = db.Column(db.DateTime)
    domain = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    task = db.relationship('SearchTask', backref='results')
    
    def extract_python_list(self, text):
        """
        Извлекает Python список из текста, даже если есть лишний текст до или после.
        Возвращает список или None.
        """
        try:
            # Ищем что-то похожее на Python список в тексте
            list_pattern = r'\[(.*?)\]'
            match = re.search(list_pattern, text)
            if match:
                list_str = match.group(0)
                # Пробуем выполнить eval для найденного списка
                result = eval(list_str)
                if isinstance(result, list):
                    return result
            return None
        except:
            return None

    def clean_list_item(self, item):
        """
        Очищает элемент списка от проблемных символов и нормализует значение
        """
        if item is None:
            return 'NA'
        
        try:
            # Преобразуем в строку
            item = str(item).strip()
            
            # Заменяем проблемные символы
            item = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', item)
            
            # Нормализуем пустые значения
            if not item or item.lower() in ['none', 'null', 'nan', 'undefined', '']:
                return 'NA'
            
            # Нормализуем числовые значения
            if isinstance(item, (int, float)):
                return str(item)
                
            return item
        except:
            return 'NA'

    def parse_analysis(self):
        """
        Парсит ответ LLM в словарь, где ключи - названия колонок из промпта
        """
        if not self.analysis or not self.task.prompt:
            return {field.name: 'NA' for field in self.task.prompt.fields}
            
        try:
            # Получаем поля промпта в правильном порядке
            fields = PromptField.query.filter_by(
                prompt_id=self.task.prompt_id
            ).order_by(PromptField.order).all()
            
            if not fields:
                return {}
            
            # Сначала пробуем напрямую распарсить как список
            try:
                analysis_list = eval(self.analysis)
            except:
                # Если не получилось, пытаемся найти список в тексте
                analysis_list = self.extract_python_list(self.analysis)
            
            # Если не удалось получить список, возвращаем NA для всех полей
            if not analysis_list or not isinstance(analysis_list, list):
                return {field.name: 'NA' for field in fields}
            
            # Создаем словарь, сопоставляя значения с названиями полей
            result = {}
            for i, field in enumerate(fields):
                try:
                    # Получаем значение из списка или NA, если индекс за пределами
                    value = analysis_list[i] if i < len(analysis_list) else 'NA'
                    # Очищаем и нормализуем значение
                    result[field.name] = self.clean_list_item(value)
                except:
                    result[field.name] = 'NA'
                
            return result
            
        except Exception as e:
            print(f"Error parsing analysis for result {self.id}: {str(e)}")
            return {field.name: 'NA' for field in fields}
