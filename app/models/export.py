from app import db
from datetime import datetime

class Export(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('search_task.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_size = db.Column(db.Integer)  # размер в байтах
    row_count = db.Column(db.Integer)  # количество строк
    
    task = db.relationship('SearchTask', backref=db.backref('exports', lazy=True)) 