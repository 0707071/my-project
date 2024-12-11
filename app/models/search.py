from datetime import datetime
from app import db

class SearchQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    main_phrases = db.Column(db.Text, nullable=False)
    include_words = db.Column(db.Text)
    exclude_words = db.Column(db.Text)
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Добавляем новые поля с дефолтными значениями
    days_back = db.Column(db.Integer, default=7)
    results_per_page = db.Column(db.Integer, default=10)
    num_pages = db.Column(db.Integer, default=1)

    client = db.relationship('Client', backref=db.backref('search_queries', lazy=True))
    tasks = db.relationship('SearchTask', backref='search_query', lazy=True) 