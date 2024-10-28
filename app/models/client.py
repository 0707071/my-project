from app import db
from datetime import datetime

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Связи
    search_queries = db.relationship('SearchQuery', backref='client', lazy='dynamic')
    prompts = db.relationship('Prompt', backref='client', lazy='dynamic')
    
    def __repr__(self):
        return f'<Client {self.name}>'
