from app import db
from datetime import datetime

class Prompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    version = db.Column(db.Integer, default=1)
    content = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Связи
    created_by = db.relationship('User', backref='prompts')
    fields = db.relationship('PromptField', 
                           backref=db.backref('parent_prompt', lazy=True),
                           order_by='PromptField.order',
                           cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Prompt {self.id} v{self.version}>'

class PromptField(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prompt_id = db.Column(db.Integer, db.ForeignKey('prompt.id'), nullable=False)
    name = db.Column(db.String(100))  # Название колонки
    order = db.Column(db.Integer)  # Порядок в ответе
    
    def __repr__(self):
        return f'<PromptField {self.name}>'
