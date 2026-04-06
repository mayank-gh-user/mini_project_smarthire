from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Company(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    company_name = db.Column(db.String(120), nullable=False)
    jobs = db.relationship('Job', backref='employer', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    required_skills = db.Column(db.Text, nullable=False) # Pipe separated: "Python|Flask|SQL"
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    candidate_name = db.Column(db.String(100), nullable=True)
    extracted_skills = db.Column(db.Text, nullable=False) # Pipe separated or JSON
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(100), nullable=False) # Can be 'db_ID' or CSV row index/ID
    candidate_name = db.Column(db.String(100), nullable=False)
    candidate_email = db.Column(db.String(120), nullable=False)
    resume_filename = db.Column(db.String(120), nullable=True)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
