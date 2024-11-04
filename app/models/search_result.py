from app import db
from datetime import datetime

class SearchResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('search_task.id'), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(500))
    snippet = db.Column(db.Text)
    content = db.Column(db.Text)
    analysis = db.Column(db.Text)  # Сырой ответ LLM
    published_date = db.Column(db.DateTime)
    domain = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Поля для разобранного анализа
    company_name = db.Column(db.String(255))  # Название компании
    potential_score = db.Column(db.Integer)  # Оценка потенциала (0-4)
    sales_notes = db.Column(db.Text)  # Заметки для отдела продаж
    company_description = db.Column(db.Text)  # Краткое описание компании
    annual_revenue = db.Column(db.Float)  # Предполагаемый годовой доход в млн $
    country = db.Column(db.String(100))  # Страна штаб-квартиры
    website = db.Column(db.String(255))  # Сайт компании
    assumed_website = db.Column(db.String(255))  # Предполагаемый сайт
    
    # Связи
    task = db.relationship('SearchTask', backref='results')
    
    def __repr__(self):
        return f'<SearchResult {self.id}>'
