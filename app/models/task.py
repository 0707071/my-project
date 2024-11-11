from app import db
from datetime import datetime
import os

class SearchTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    search_query_id = db.Column(db.Integer, db.ForeignKey('search_query.id'), nullable=False)
    prompt_id = db.Column(db.Integer, db.ForeignKey('prompt.id'))
    prompt = db.relationship('Prompt', backref='tasks')
    celery_task_id = db.Column(db.String(36), unique=True)
    status = db.Column(db.String(20), default='pending')  # pending, searching, cleaning, analyzing, completed, failed
    stage = db.Column(db.String(20), default='search')  # search, clean, analyze
    progress = db.Column(db.Integer, default=0)
    result_file = db.Column(db.String(255))
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<SearchTask {self.id}>'

    def get_latest_result_file(self):
        """Returns path to the latest result file"""
        if self.result_file and os.path.exists(self.result_file):
            return self.result_file
        return None
