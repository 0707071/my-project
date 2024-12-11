from app import db
from datetime import datetime

class SearchQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    version = db.Column(db.Integer, default=1)
    main_phrases = db.Column(db.Text)
    include_words = db.Column(db.Text)
    exclude_words = db.Column(db.Text)
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Добавляем настройки поиска
    days_back = db.Column(db.Integer, default=7)
    results_per_page = db.Column(db.Integer, default=100)
    num_pages = db.Column(db.Integer, default=2)
    
    # Добавляем связь с задачами
    tasks = db.relationship('SearchTask', backref='search_query', lazy='dynamic')
    
    def __repr__(self):
        return f'<SearchQuery {self.id} v{self.version}>'
