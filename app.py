import os

from datetime import datetime

from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify

from flask_sqlalchemy import SQLAlchemy

from flask_migrate import Migrate

from werkzeug.security import generate_password_hash, check_password_hash

from werkzeug.middleware.proxy_fix import ProxyFix

from functools import wraps

import logging

import time

# Configure logging

logger = logging.getLogger('azure_quiz_app')

logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

handler = logging.StreamHandler()

handler.setFormatter(formatter)

logger.addHandler(handler)

# Create Flask app

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'azure_quiz_secret_key')

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {

    'pool_size': 5,

    'pool_timeout': 10,

    'pool_recycle': 60,

    'max_overflow': 10,

    'pool_pre_ping': True,

    'connect_args': {

        'connect_timeout': 10,

        'keepalives': 1,

        'keepalives_idle': 30,

        'keepalives_interval': 10,

        'keepalives_count': 5

    }

}

# Enable proxy support for proper IP handling

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Request performance monitoring middleware

@app.before_request

def before_request():

    session['start_time'] = time.time()


@app.after_request

def after_request(response):

    if 'start_time' in session:

        request_duration = time.time() - session.pop('start_time')

        # Log slow requests (>500ms)

        if request_duration > 0.5:

            logger.warning(f"Slow request: {request.path} took {request_duration:.2f}s")

    return response

# Initialize database

db = SQLAlchemy(app)

migrate = Migrate(app, db)

# Import models

from models import Admin, Guest, Quiz, Question, Option, Result, Improvement, CertificationType, QuizDifficulty

# Admin authentication decorator

def admin_required(f):

    @wraps(f)

    def decorated_function(*args, **kwargs):

        if 'admin_id' not in session:

            flash('Please log in as admin to access this page', 'danger')

            return redirect(url_for('admin_login'))

        return f(*args, **kwargs)

    return decorated_function

# Guest authentication decorator

def guest_required(f):

    @wraps(f)

    def decorated_function(*args, **kwargs):

        if 'guest_id' not in session:

            flash('Please register as a guest to access this page', 'warning')

            return redirect(url_for('guest_login'))

        return f(*args, **kwargs)

    return decorated_function

# Import routes

from routes import register_routes

# Initialize the app with routes

register_routes(app)

# Create an initial admin user if none exists

@app.before_request

def create_initial_admin():

    admin_exists = Admin.query.filter_by(username='admin').first()

    if not admin_exists:

        admin = Admin(username='admin',

                      password_hash=generate_password_hash('admin123'),

                      name='Administrator',

                      email='admin@example.com')

        db.session.add(admin)

        # Create sample quizzes and questions for Azure AI-900

        create_sample_quizzes()

        db.session.commit()

        logging.info("Created initial admin and sample quizzes")

def create_sample_quizzes():

    # Create certification types

    certifications = [{

        'code': 'AI-900',

        'name': 'Azure AI Fundamentals',

        'description': 'Foundation-level knowledge of machine learning and AI in Microsoft Azure'

    }, {

        'code': 'AZ-104',

        'name': 'Azure Administrator',

        'description': 'Implementation, management, and monitoring of Microsoft Azure environment'

    }, {

        'code': 'AZ-400',

        'name': 'DevOps Engineer Expert',

        'description': 'Designing and implementing strategies for collaboration, code, infrastructure, source control, security, compliance, continuous integration, testing, delivery, monitoring, and feedback'

    }]

    created_certifications = {}

    for cert_data in certifications:

        # Check if certification already exists

        cert = CertificationType.query.filter_by(code=cert_data['code']).first()

        if not cert:

            cert = CertificationType(code=cert_data['code'],

                                     name=cert_data['name'],

                                     description=cert_data['description'])

            db.session.add(cert)

            db.session.flush()  # Get the ID

        created_certifications[cert_data['code']] = cert

    # Create Azure AI-900 quiz

    azure_quiz = Quiz(

        title='Azure Certifications',

        description='Test your knowledge of Microsoft Azure AI Fundamentals concepts',

        time_limit=30,  # 30 minutes

        pass_percentage=70,

        difficulty=QuizDifficulty.MEDIUM,

        certification_id=created_certifications['AI-900'].id,

        is_active=True)

    db.session.add(azure_quiz)

    db.session.flush()  # To get the ID

    # Sample questions for Azure AI-900

    questions = [{

        'text': 'Which Azure service would you use for natural language processing?',

        'explanation': 'Azure Cognitive Services Text Analytics provides natural language processing capabilities.',

        'options': [{

            'text': 'Azure Cognitive Services Text Analytics',

            'is_correct': True

        }, {

            'text': 'Azure Machine Learning',

            'is_correct': False

        }, {

            'text': 'Azure Logic Apps',

            'is_correct': False

        }, {

            'text': 'Azure Functions',

            'is_correct': False

        }]

    }, {

        'text': 'What is the primary purpose of Azure Machine Learning?',

        'explanation': 'Azure Machine Learning is a cloud-based service that helps data scientists and developers build, train, and deploy machine learning models.',

        'options': [{

            'text': 'To host web applications',

            'is_correct': False

        }, {

            'text': 'To build, train, and deploy machine learning models',

            'is_correct': True

        }, {

            'text': 'To manage database services',

            'is_correct': False

        }, {

            'text': 'To provide network security',

            'is_correct': False

        }]

    }]

    # Add each question and its options

    for q_data in questions:

        question = Question(quiz_id=azure_quiz.id,

                            text=q_data['text'],

                            explanation=q_data['explanation'])

        db.session.add(question)

        db.session.flush()  # To get the ID

        # Add options for the question

        for o_data in q_data['options']:

            option = Option(question_id=question.id,

                            text=o_data['text'],

                            is_correct=o_data['is_correct'])

            db.session.add(option)

    # Create some standard improvement areas

    improvement_areas = [

        "Review Azure Cognitive Services documentation for better understanding of available AI capabilities.",

        "Practice using Azure Machine Learning to build and deploy models.",

        "Learn more about responsible AI principles and their application.",

        "Explore Azure Bot Service and build a simple chatbot to understand the concepts.",

        "Study computer vision capabilities in Azure and their practical applications."

    ]

    for area in improvement_areas:

        improvement = Improvement(quiz_id=azure_quiz.id, description=area)

        db.session.add(improvement)

if __name__ == '__main__':

    port = int(os.environ.get('PORT', 5000))

    app.run(host='0.0.0.0', port=port, debug=True)
