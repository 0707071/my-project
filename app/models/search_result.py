from app import db
from datetime import datetime

class SearchResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('search_task.id'), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(500))
    snippet = db.Column(db.Text)
    content = db.Column(db.Text)
    published_date = db.Column(db.DateTime)
    domain = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    task = db.relationship('SearchTask', backref='results')
    
    def __repr__(self):
        return f'<SearchResult {self.id}>'
