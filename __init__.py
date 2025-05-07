import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'azure_quiz_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    with app.app_context():
        # Import routes and models
        from . import models, routes
        
        # Register routes
        routes.register_routes(app)
        
        # Create tables
        db.create_all()
        
        # Create admin user and sample certification types if none exist
        from .models import Admin, CertificationType
        from werkzeug.security import generate_password_hash
        
        admin_exists = Admin.query.filter_by(username='admin').first()
        certs_exist = CertificationType.query.first()
        
        if not admin_exists or not certs_exist:
            # Create admin user if it doesn't exist
            if not admin_exists:
                admin = Admin(
                    username='admin',
                    password_hash=generate_password_hash('admin123'),
                    name='Administrator',
                    email='admin@example.com'
                )
                db.session.add(admin)
            
            # Create certification types if they don't exist
            if not certs_exist:
                create_certification_types()
            
            # Create sample quizzes for testing
            create_sample_quizzes()
            
            db.session.commit()
            logging.info("Created initial admin, certification types, and sample quizzes")
    
    return app

def create_certification_types():
    """Create initial certification types for Azure exams"""
    from .models import CertificationType
    
    certifications = [
        {
            'name': 'Azure AI-900: Azure AI Fundamentals',
            'code': 'AI-900',
            'description': 'Certification for fundamental knowledge of machine learning and artificial intelligence concepts in Azure.'
        },
        {
            'name': 'Azure AZ-104: Azure Administrator',
            'code': 'AZ-104',
            'description': 'Certification for IT Professionals who manage Azure subscriptions and resources, implement and monitor cloud infrastructure.'
        },
        {
            'name': 'Azure AZ-400: DevOps Engineer Expert',
            'code': 'AZ-400',
            'description': 'Certification for DevOps professionals who combine people, process, and technologies to deliver products and services.'
        }
    ]
    
    for cert_data in certifications:
        certification = CertificationType(
            name=cert_data['name'],
            code=cert_data['code'],
            description=cert_data['description']
        )
        db.session.add(certification)
    
    db.session.flush()  # To get the IDs of the newly created certifications

def create_sample_quizzes():
    from .models import Quiz, Question, Option, Improvement, QuizDifficulty, CertificationType
    
    # Get certification types
    ai_900_cert = CertificationType.query.filter_by(code='AI-900').first()
    az_104_cert = CertificationType.query.filter_by(code='AZ-104').first()
    az_400_cert = CertificationType.query.filter_by(code='AZ-400').first()
    
    if not all([ai_900_cert, az_104_cert, az_400_cert]):
        logging.error("Certification types not found. Cannot create quizzes.")
        return
    
    # Create Azure AI-900 quiz
    azure_quiz = Quiz(
        certification_id=ai_900_cert.id,
        title='Azure AI-900 Fundamentals',
        description='Test your knowledge of Microsoft Azure AI Fundamentals concepts',
        time_limit=30,  # 30 minutes
        pass_percentage=70,
        is_active=True
    )
    db.session.add(azure_quiz)
    db.session.flush()  # To get the ID
    
    # Sample questions for Azure AI-900
    questions = [
        {
            'text': 'Which Azure service would you use for natural language processing?',
            'explanation': 'Azure Cognitive Services Text Analytics provides natural language processing capabilities.',
            'options': [
                {'text': 'Azure Cognitive Services Text Analytics', 'is_correct': True},
                {'text': 'Azure Machine Learning', 'is_correct': False},
                {'text': 'Azure Logic Apps', 'is_correct': False},
                {'text': 'Azure Functions', 'is_correct': False}
            ]
        },
        {
            'text': 'What is the primary purpose of Azure Machine Learning?',
            'explanation': 'Azure Machine Learning is a cloud-based service that helps data scientists and developers build, train, and deploy machine learning models.',
            'options': [
                {'text': 'To host web applications', 'is_correct': False},
                {'text': 'To build, train, and deploy machine learning models', 'is_correct': True},
                {'text': 'To manage database services', 'is_correct': False},
                {'text': 'To provide network security', 'is_correct': False}
            ]
        },
        {
            'text': 'Which Azure service is designed specifically for computer vision tasks?',
            'explanation': 'Azure Computer Vision is part of Cognitive Services and provides image processing algorithms to analyze visual content.',
            'options': [
                {'text': 'Azure SQL Database', 'is_correct': False},
                {'text': 'Azure Computer Vision', 'is_correct': True},
                {'text': 'Azure Virtual Machines', 'is_correct': False},
                {'text': 'Azure App Service', 'is_correct': False}
            ]
        },
        {
            'text': 'What is Azure Cognitive Services?',
            'explanation': 'Azure Cognitive Services are cloud-based AI services that help developers add cognitive features to their applications without requiring machine learning expertise.',
            'options': [
                {'text': 'A set of virtual machines optimized for deep learning', 'is_correct': False},
                {'text': 'A database service for storing AI models', 'is_correct': False},
                {'text': 'A collection of pre-built AI services that can be easily integrated into applications', 'is_correct': True},
                {'text': 'A tool for monitoring AI application performance', 'is_correct': False}
            ]
        },
        {
            'text': 'Which Azure service would you use to create and deploy a chatbot?',
            'explanation': 'Azure Bot Service provides an integrated environment to build, test, and deploy chatbots.',
            'options': [
                {'text': 'Azure Storage', 'is_correct': False},
                {'text': 'Azure Bot Service', 'is_correct': True},
                {'text': 'Azure Kubernetes Service', 'is_correct': False},
                {'text': 'Azure DevOps', 'is_correct': False}
            ]
        },
        {
            'text': 'What is responsible AI?',
            'explanation': 'Responsible AI is an approach to developing and deploying AI systems in a manner that is ethical, transparent, accountable, and centered on human values.',
            'options': [
                {'text': 'AI systems that work correctly without bugs', 'is_correct': False},
                {'text': 'The practice of having human oversight for all AI decisions', 'is_correct': False},
                {'text': 'A framework for ensuring AI systems are ethical, transparent, and accountable', 'is_correct': True},
                {'text': 'A certification program for AI developers', 'is_correct': False}
            ]
        },
        {
            'text': 'Which of the following is a feature of Azure Form Recognizer?',
            'explanation': 'Azure Form Recognizer can extract text, key-value pairs, tables, and structures from documents.',
            'options': [
                {'text': 'Creating animated forms for websites', 'is_correct': False},
                {'text': 'Extracting text and structure from documents', 'is_correct': True},
                {'text': 'Validating web form inputs', 'is_correct': False},
                {'text': 'Encrypting form data', 'is_correct': False}
            ]
        },
        {
            'text': 'What does MLOps stand for?',
            'explanation': 'MLOps (Machine Learning Operations) is a practice for collaboration and communication between data scientists and operations professionals.',
            'options': [
                {'text': 'Machine Learning Operations', 'is_correct': True},
                {'text': 'Multiple Learning Optimization', 'is_correct': False},
                {'text': 'Meta Language for Operation Systems', 'is_correct': False},
                {'text': 'Microsoft Learning Options', 'is_correct': False}
            ]
        },
        {
            'text': 'Which Azure service provides capabilities for speech-to-text conversion?',
            'explanation': 'Azure Speech Service provides capabilities to convert speech-to-text and text-to-speech.',
            'options': [
                {'text': 'Azure Text Analytics', 'is_correct': False},
                {'text': 'Azure Speech Service', 'is_correct': True},
                {'text': 'Azure Translator', 'is_correct': False},
                {'text': 'Azure Content Moderator', 'is_correct': False}
            ]
        },
        {
            'text': 'What is the primary benefit of using pre-built AI models in Azure Cognitive Services?',
            'explanation': 'Pre-built AI models in Azure Cognitive Services allow you to implement AI capabilities without requiring deep AI expertise or extensive training data.',
            'options': [
                {'text': 'They are free to use without any charges', 'is_correct': False},
                {'text': 'They can be implemented without any programming', 'is_correct': False},
                {'text': 'They can be used without requiring deep AI expertise or training data', 'is_correct': True},
                {'text': 'They work offline without an internet connection', 'is_correct': False}
            ]
        }
    ]
    
    # Add each question and its options
    for q_data in questions:
        question = Question(
            quiz_id=azure_quiz.id,
            text=q_data['text'],
            explanation=q_data['explanation']
        )
        db.session.add(question)
        db.session.flush()  # To get the ID
        
        # Add options for the question
        for o_data in q_data['options']:
            option = Option(
                question_id=question.id,
                text=o_data['text'],
                is_correct=o_data['is_correct']
            )
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
        improvement = Improvement(
            quiz_id=azure_quiz.id,
            description=area
        )
        db.session.add(improvement)
        
    # Create Azure AZ-104 quiz
    az104_quiz = Quiz(
        certification_id=az_104_cert.id,
        title='Azure AZ-104 Administrator',
        description='Test your knowledge of Azure administration and management tasks',
        time_limit=40,  # 40 minutes
        pass_percentage=70,
        is_active=True
    )
    db.session.add(az104_quiz)
    db.session.flush()
    
    # Sample AZ-104 questions
    az104_questions = [
        {
            'text': 'Which Azure service would you use to store unstructured data such as text or binary data?',
            'explanation': 'Azure Blob Storage is designed for storing massive amounts of unstructured data, such as text or binary data.',
            'options': [
                {'text': 'Azure Blob Storage', 'is_correct': True},
                {'text': 'Azure SQL Database', 'is_correct': False},
                {'text': 'Azure Table Storage', 'is_correct': False},
                {'text': 'Azure Cosmos DB', 'is_correct': False}
            ]
        },
        {
            'text': 'What Azure tool would you use to get a monthly estimate of your Azure spending?',
            'explanation': 'Azure Cost Management provides tools to monitor, allocate, and optimize your Azure costs.',
            'options': [
                {'text': 'Azure Advisor', 'is_correct': False},
                {'text': 'Azure Cost Management', 'is_correct': True},
                {'text': 'Azure Policy', 'is_correct': False},
                {'text': 'Azure Monitor', 'is_correct': False}
            ]
        },
        {
            'text': 'Which Azure service would you use to automatically scale applications based on demand?',
            'explanation': 'Azure Autoscale allows you to dynamically scale your applications based on demand to maintain performance and control costs.',
            'options': [
                {'text': 'Azure Load Balancer', 'is_correct': False},
                {'text': 'Azure Traffic Manager', 'is_correct': False},
                {'text': 'Azure Autoscale', 'is_correct': True},
                {'text': 'Azure CDN', 'is_correct': False}
            ]
        }
    ]
    
    # Add AZ-104 questions and options
    for q_data in az104_questions:
        question = Question(
            quiz_id=az104_quiz.id,
            text=q_data['text'],
            explanation=q_data['explanation']
        )
        db.session.add(question)
        db.session.flush()
        
        for o_data in q_data['options']:
            option = Option(
                question_id=question.id,
                text=o_data['text'],
                is_correct=o_data['is_correct']
            )
            db.session.add(option)
    
    # AZ-104 improvement areas
    az104_improvements = [
        "Study Azure Storage solutions and their appropriate use cases.",
        "Practice configuring and managing virtual networks in Azure.",
        "Learn about Azure identity services and access management.",
        "Explore Azure resource management and governance tools."
    ]
    
    for area in az104_improvements:
        improvement = Improvement(
            quiz_id=az104_quiz.id,
            description=area
        )
        db.session.add(improvement)
    
    # Create Azure AZ-400 quiz
    az400_quiz = Quiz(
        certification_id=az_400_cert.id,
        title='Azure AZ-400 DevOps Engineer',
        description='Test your knowledge of DevOps practices with Azure DevOps tools',
        time_limit=45,  # 45 minutes
        pass_percentage=70,
        is_active=True
    )
    db.session.add(az400_quiz)
    db.session.flush()
    
    # Sample AZ-400 questions
    az400_questions = [
        {
            'text': 'Which Azure DevOps service would you use for continuous integration and continuous delivery (CI/CD)?',
            'explanation': 'Azure Pipelines is a cloud service that you can use to automatically build, test, and deploy your code project.',
            'options': [
                {'text': 'Azure Boards', 'is_correct': False},
                {'text': 'Azure Repos', 'is_correct': False},
                {'text': 'Azure Pipelines', 'is_correct': True},
                {'text': 'Azure Test Plans', 'is_correct': False}
            ]
        },
        {
            'text': 'Which tool would you use to track work items in Azure DevOps?',
            'explanation': 'Azure Boards is used to track work items, including user stories, bugs, and tasks.',
            'options': [
                {'text': 'Azure Boards', 'is_correct': True},
                {'text': 'Azure Repos', 'is_correct': False},
                {'text': 'Azure Pipelines', 'is_correct': False},
                {'text': 'Azure Artifacts', 'is_correct': False}
            ]
        },
        {
            'text': 'What is the purpose of Infrastructure as Code (IaC)?',
            'explanation': 'Infrastructure as Code allows you to manage infrastructure through code instead of manual processes.',
            'options': [
                {'text': 'To eliminate the need for servers', 'is_correct': False},
                {'text': 'To manage infrastructure through code instead of manual processes', 'is_correct': True},
                {'text': 'To automatically generate documentation', 'is_correct': False},
                {'text': 'To reduce the cost of cloud infrastructure', 'is_correct': False}
            ]
        }
    ]
    
    # Add AZ-400 questions and options
    for q_data in az400_questions:
        question = Question(
            quiz_id=az400_quiz.id,
            text=q_data['text'],
            explanation=q_data['explanation']
        )
        db.session.add(question)
        db.session.flush()
        
        for o_data in q_data['options']:
            option = Option(
                question_id=question.id,
                text=o_data['text'],
                is_correct=o_data['is_correct']
            )
            db.session.add(option)
    
    # AZ-400 improvement areas
    az400_improvements = [
        "Practice implementing CI/CD pipelines using Azure Pipelines.",
        "Learn about infrastructure as code using Azure ARM templates or Terraform.",
        "Study DevOps practices for security and compliance in Azure.",
        "Explore monitoring and feedback mechanisms in Azure DevOps."
    ]
    
    for area in az400_improvements:
        improvement = Improvement(
            quiz_id=az400_quiz.id,
            description=area
        )
        db.session.add(improvement)