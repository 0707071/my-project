from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum

# Define the Role Enum
class Role(Enum):
    CLIENT = 'client'
    ANALYST = 'analyst'

class User(UserMixin, db.Model):
    __tablename__ = 'user'  # Specify the table name explicitly

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.Enum(Role), nullable=False, default=Role.CLIENT)  # Ensure this matches the ENUM type

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))