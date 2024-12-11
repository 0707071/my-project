from app import db
from datetime import datetime

class AnalysisResult(db.Model):
    __tablename__ = 'analysis_result'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('search_task.id'), nullable=False)
    prompt_id = db.Column(db.Integer, db.ForeignKey('prompt.id'), nullable=False)
    
    # Исходные данные
    title = db.Column(db.String(500))
    url = db.Column(db.String(500))
    content = db.Column(db.Text)
    
    # Результаты анализа
    company_name = db.Column(db.String(200))
    potential = db.Column(db.Integer)
    sales_notes = db.Column(db.Text)
    company_description = db.Column(db.Text)
    revenue = db.Column(db.Float)
    country = db.Column(db.String(100))
    website = db.Column(db.String(500))
    
    # Метаданные
    article_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Добавим связи
    task = db.relationship('SearchTask', backref=db.backref('analysis_results', lazy=True))
    prompt = db.relationship('Prompt', backref=db.backref('analysis_results', lazy=True))
    
    def to_dict(self):
        return {
            'company_name': self.company_name,
            'potential': self.potential,
            'sales_notes': self.sales_notes,
            'company_description': self.company_description,
            'revenue': self.revenue,
            'country': self.country,
            'website': self.website
        } 