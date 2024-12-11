from app import db
from datetime import datetime

class SearchResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('search_task.id'), nullable=False)
    url = db.Column(db.String(500))
    title = db.Column(db.Text)
    content = db.Column(db.Text)
    analysis = db.Column(db.Text)
    published_date = db.Column(db.DateTime)
    domain = db.Column(db.String(255))
    snippet = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    task = db.relationship('SearchTask', backref=db.backref('results', lazy=True))
    
    def parse_analysis(self):
        """Parse the analysis string into a dictionary"""
        try:
            if not self.analysis:
                return {}
            # Предполагаем, что анализ сохранен как строковое представление списка Python
            analysis_list = eval(self.analysis)
            return {
                'Company Name': analysis_list[0],
                'Score': analysis_list[1],
                'Notes': analysis_list[2],
                'Description': analysis_list[3],
                'Revenue': analysis_list[4],
                'Country': analysis_list[5],
                'Website': analysis_list[6]
            }
        except:
            return {}
