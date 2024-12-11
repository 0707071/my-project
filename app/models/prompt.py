from app import db
from datetime import datetime

class Prompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    column_names = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Prompt for Client {self.client_id}>'
