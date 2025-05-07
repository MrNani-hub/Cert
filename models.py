from datetime import datetime
from enum import Enum
from app import db

# Enums
class QuizDifficulty(Enum):
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'

class CertificationType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)  # e.g., "Azure AI-900", "Azure AZ-104", "Azure AZ-400"
    code = db.Column(db.String(20), unique=True, nullable=False)  # e.g., "AI-900", "AZ-104", "AZ-400"
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    quizzes = db.relationship('Quiz', backref='certification', lazy=True)
    
    def __repr__(self):
        return f'<Certification {self.code}>'

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Admin {self.username}>'

class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with results
    results = db.relationship('Result', backref='guest', lazy=True)
    
    def __repr__(self):
        return f'<Guest {self.name}>'

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    certification_id = db.Column(db.Integer, db.ForeignKey('certification_type.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    time_limit = db.Column(db.Integer, nullable=False)  # in minutes
    pass_percentage = db.Column(db.Integer, nullable=False, default=70)
    is_active = db.Column(db.Boolean, default=True)
    difficulty = db.Column(db.Enum(QuizDifficulty), default=QuizDifficulty.MEDIUM)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('Question', backref='quiz', lazy=True, cascade='all, delete-orphan')
    results = db.relationship('Result', backref='quiz', lazy=True)
    improvements = db.relationship('Improvement', backref='quiz', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Quiz {self.title}>'
    
    @property
    def question_count(self):
        return len(self.questions)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    options = db.relationship('Option', backref='question', lazy=True, cascade='all, delete-orphan')
    answers = db.relationship('Answer', backref='question', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Question {self.id}>'

class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Option {self.id}>'

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    score = db.Column(db.Integer, nullable=True)  # null until quiz is completed
    total_questions = db.Column(db.Integer, nullable=False)
    percentage = db.Column(db.Float, nullable=True)  # null until quiz is completed
    passed = db.Column(db.Boolean, nullable=True)  # null until quiz is completed
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    time_taken = db.Column(db.Integer, nullable=True)  # in seconds
    
    # Relationships
    answers = db.relationship('Answer', backref='result', lazy=True, cascade='all, delete-orphan')
    suggested_improvements = db.relationship('SuggestedImprovement', backref='result', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Result {self.id}>'

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey('result.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    selected_option_id = db.Column(db.Integer, db.ForeignKey('option.id'), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    
    # Relationship
    selected_option = db.relationship('Option', foreign_keys=[selected_option_id])
    
    def __repr__(self):
        return f'<Answer {self.id}>'

class Improvement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    def __repr__(self):
        return f'<Improvement {self.id}>'

class SuggestedImprovement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey('result.id'), nullable=False)
    improvement_id = db.Column(db.Integer, db.ForeignKey('improvement.id'), nullable=False)
    
    # Relationship
    improvement = db.relationship('Improvement')
    
    def __repr__(self):
        return f'<SuggestedImprovement {self.id}>'
