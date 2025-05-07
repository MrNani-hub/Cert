from flask import render_template, redirect, url_for, flash, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random
import functools
import time
import logging
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from . import db
from models import (Admin, Guest, Quiz, Question, Option, Result, Answer, 
                   Improvement, SuggestedImprovement, QuizDifficulty, CertificationType)

# Configure route logging
logger = logging.getLogger('azure_quiz_app.routes')
logger.setLevel(logging.DEBUG)

# Function to retry database operations if they fail due to connection issues
def retry_db_operation(func):
    """Decorator to retry database operations on connection failure"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 3
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except (OperationalError, SQLAlchemyError) as e:
                # Only retry on connection-related errors
                if "connection" not in str(e).lower() and "ssl" not in str(e).lower():
                    raise
                
                if attempt < max_retries - 1:  # Don't sleep on the last attempt
                    logger.warning(f"Database connection error, retrying ({attempt+1}/{max_retries}): {str(e)}")
                    try:
                        db.session.rollback()
                    except:
                        pass  # If rollback fails, just continue
                    
                    # Exponential backoff
                    sleep_time = retry_delay * (2 ** attempt)
                    time.sleep(sleep_time)
                else:
                    logger.error(f"Failed to execute database operation after {max_retries} attempts: {str(e)}")
                    # Create a user-friendly error page instead of 500 error
                    return render_template('errors/500.html', 
                                          error_message="We're experiencing database connectivity issues. Please try again in a moment."), 500
        
        return func(*args, **kwargs)  # Final attempt
    return wrapper

# Admin authentication decorator
def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please log in as admin to access this page', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Guest authentication decorator
def guest_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'guest_id' not in session:
            flash('Please register as a guest to access this page', 'warning')
            return redirect(url_for('guest_login'))
        return f(*args, **kwargs)
    return decorated_function

def register_routes(app):
    
    @app.context_processor
    def inject_date():
        return {'now': datetime.utcnow()}
    
    # Home page
    @app.route('/')
    def index():
        # Redirect to appropriate dashboard if already logged in
        if 'admin_id' in session:
            return redirect(url_for('admin_dashboard'))
        elif 'guest_id' in session:
            return redirect(url_for('guest_quizzes'))
        
        return render_template('index.html')
    
    # Admin login
    @app.route('/admin/login', methods=['GET', 'POST'])
    @retry_db_operation
    def admin_login():
        # Redirect to admin dashboard if already logged in as admin
        if 'admin_id' in session:
            return redirect(url_for('admin_dashboard'))
            
        # If user is logged in as guest, log them out first
        if 'guest_id' in session:
            session.pop('guest_id', None)
            flash('You have been logged out as guest to access admin area', 'info')
            
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            admin = Admin.query.filter_by(username=username).first()
            
            if admin and check_password_hash(admin.password_hash, password):
                session['admin_id'] = admin.id
                flash('You have been logged in successfully as administrator!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid username or password', 'danger')
        
        return render_template('admin/login.html')
    
    # Admin logout
    @app.route('/admin/logout')
    def admin_logout():
        session.pop('admin_id', None)
        flash('You have been logged out', 'success')
        return redirect(url_for('index'))
    
    # Admin dashboard
    @app.route('/admin/dashboard')
    @admin_required
    @retry_db_operation
    def admin_dashboard():
        quizzes = Quiz.query.all()
        total_guests = Guest.query.count()
        total_results = Result.query.count()
        
        return render_template('admin/dashboard.html', 
                               quizzes=quizzes, 
                               total_guests=total_guests, 
                               total_results=total_results)
    
    # Admin manage quizzes
    @app.route('/admin/quizzes')
    @admin_required
    @retry_db_operation
    def admin_quizzes():
        quizzes = Quiz.query.all()
        certifications = CertificationType.query.all()
        return render_template('admin/quizzes.html', quizzes=quizzes, certifications=certifications)
    
    # Admin add quiz
    @app.route('/admin/quizzes/add', methods=['GET', 'POST'])
    @admin_required
    def admin_add_quiz():
        certifications = CertificationType.query.all()
        
        if request.method == 'POST':
            title = request.form.get('title')
            description = request.form.get('description')
            certification_id = int(request.form.get('certification_id'))
            time_limit = int(request.form.get('time_limit'))
            pass_percentage = int(request.form.get('pass_percentage'))
            difficulty = request.form.get('difficulty', 'medium')
            is_active = 'is_active' in request.form
            
            quiz = Quiz(
                title=title,
                description=description,
                certification_id=certification_id,
                time_limit=time_limit,
                pass_percentage=pass_percentage,
                difficulty=QuizDifficulty(difficulty),
                is_active=is_active
            )
            
            db.session.add(quiz)
            db.session.commit()
            
            flash(f'Quiz "{title}" has been added!', 'success')
            return redirect(url_for('admin_edit_quiz', quiz_id=quiz.id))
        
        return render_template('admin/add_quiz.html', certifications=certifications)
    
    # Admin edit quiz
    @app.route('/admin/quizzes/<int:quiz_id>/edit', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_quiz(quiz_id):
        quiz = Quiz.query.get_or_404(quiz_id)
        certifications = CertificationType.query.all()
        
        if request.method == 'POST':
            quiz.title = request.form.get('title')
            quiz.description = request.form.get('description')
            quiz.certification_id = int(request.form.get('certification_id'))
            quiz.time_limit = int(request.form.get('time_limit'))
            quiz.pass_percentage = int(request.form.get('pass_percentage'))
            quiz.difficulty = QuizDifficulty(request.form.get('difficulty', 'medium'))
            quiz.is_active = 'is_active' in request.form
            
            db.session.commit()
            flash('Quiz has been updated!', 'success')
            return redirect(url_for('admin_quizzes'))
        
        return render_template('admin/edit_quiz.html', quiz=quiz, certifications=certifications)
    
    # Admin delete quiz
    @app.route('/admin/quizzes/<int:quiz_id>/delete', methods=['POST'])
    @admin_required
    def admin_delete_quiz(quiz_id):
        quiz = Quiz.query.get_or_404(quiz_id)
        
        db.session.delete(quiz)
        db.session.commit()
        
        flash(f'Quiz "{quiz.title}" has been deleted!', 'success')
        return redirect(url_for('admin_quizzes'))
    
    # Admin manage questions for a quiz
    @app.route('/admin/quizzes/<int:quiz_id>/questions')
    @admin_required
    def admin_questions(quiz_id):
        quiz = Quiz.query.get_or_404(quiz_id)
        questions = Question.query.filter_by(quiz_id=quiz_id).all()
        
        return render_template('admin/questions.html', quiz=quiz, questions=questions)
    
    # Admin add question
    @app.route('/admin/quizzes/<int:quiz_id>/questions/add', methods=['GET', 'POST'])
    @admin_required
    def admin_add_question(quiz_id):
        quiz = Quiz.query.get_or_404(quiz_id)
        
        if request.method == 'POST':
            text = request.form.get('text')
            explanation = request.form.get('explanation')
            
            question = Question(
                quiz_id=quiz_id,
                text=text,
                explanation=explanation
            )
            
            db.session.add(question)
            db.session.flush()  # Get the question ID
            
            # Process options
            option_texts = request.form.getlist('option_text')
            correct_option = int(request.form.get('correct_option'))
            
            for i, option_text in enumerate(option_texts):
                if option_text:  # Skip empty options
                    option = Option(
                        question_id=question.id,
                        text=option_text,
                        is_correct=(i == correct_option)
                    )
                    db.session.add(option)
            
            db.session.commit()
            flash('Question has been added!', 'success')
            return redirect(url_for('admin_questions', quiz_id=quiz_id))
        
        return render_template('admin/add_question.html', quiz=quiz)
    
    # Admin edit question
    @app.route('/admin/quizzes/<int:quiz_id>/questions/<int:question_id>/edit', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_question(quiz_id, question_id):
        quiz = Quiz.query.get_or_404(quiz_id)
        question = Question.query.get_or_404(question_id)
        
        if question.quiz_id != quiz_id:
            flash('Question does not belong to this quiz', 'danger')
            return redirect(url_for('admin_questions', quiz_id=quiz_id))
        
        options = Option.query.filter_by(question_id=question_id).all()
        
        if request.method == 'POST':
            question.text = request.form.get('text')
            question.explanation = request.form.get('explanation')
            
            # Delete existing options
            for option in options:
                db.session.delete(option)
            
            # Add new options
            option_texts = request.form.getlist('option_text')
            correct_option = int(request.form.get('correct_option'))
            
            for i, option_text in enumerate(option_texts):
                if option_text:  # Skip empty options
                    option = Option(
                        question_id=question.id,
                        text=option_text,
                        is_correct=(i == correct_option)
                    )
                    db.session.add(option)
            
            db.session.commit()
            flash('Question has been updated!', 'success')
            return redirect(url_for('admin_questions', quiz_id=quiz_id))
            
        # Find which option is correct
        correct_option_index = 0
        for i, option in enumerate(options):
            if option.is_correct:
                correct_option_index = i
                break
        
        return render_template('admin/edit_question.html', 
                              quiz=quiz, 
                              question=question, 
                              options=options, 
                              correct_option_index=correct_option_index)
    
    # Admin delete question
    @app.route('/admin/quizzes/<int:quiz_id>/questions/<int:question_id>/delete', methods=['POST'])
    @admin_required
    def admin_delete_question(quiz_id, question_id):
        question = Question.query.get_or_404(question_id)
        
        if question.quiz_id != quiz_id:
            flash('Question does not belong to this quiz', 'danger')
            return redirect(url_for('admin_questions', quiz_id=quiz_id))
        
        db.session.delete(question)
        db.session.commit()
        
        flash('Question has been deleted!', 'success')
        return redirect(url_for('admin_questions', quiz_id=quiz_id))
    
    # Admin manage improvement areas
    @app.route('/admin/quizzes/<int:quiz_id>/improvements')
    @admin_required
    def admin_improvements(quiz_id):
        quiz = Quiz.query.get_or_404(quiz_id)
        improvements = Improvement.query.filter_by(quiz_id=quiz_id).all()
        
        return render_template('admin/improvements.html', quiz=quiz, improvements=improvements)
    
    # Admin add improvement area
    @app.route('/admin/quizzes/<int:quiz_id>/improvements/add', methods=['GET', 'POST'])
    @admin_required
    def admin_add_improvement(quiz_id):
        quiz = Quiz.query.get_or_404(quiz_id)
        
        if request.method == 'POST':
            description = request.form.get('description')
            
            improvement = Improvement(
                quiz_id=quiz_id,
                description=description
            )
            
            db.session.add(improvement)
            db.session.commit()
            
            flash('Improvement area has been added!', 'success')
            return redirect(url_for('admin_improvements', quiz_id=quiz_id))
        
        return render_template('admin/add_improvement.html', quiz=quiz)
    
    # Admin edit improvement area
    @app.route('/admin/quizzes/<int:quiz_id>/improvements/<int:improvement_id>/edit', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_improvement(quiz_id, improvement_id):
        quiz = Quiz.query.get_or_404(quiz_id)
        improvement = Improvement.query.get_or_404(improvement_id)
        
        if improvement.quiz_id != quiz_id:
            flash('Improvement area does not belong to this quiz', 'danger')
            return redirect(url_for('admin_improvements', quiz_id=quiz_id))
        
        if request.method == 'POST':
            improvement.description = request.form.get('description')
            
            db.session.commit()
            flash('Improvement area has been updated!', 'success')
            return redirect(url_for('admin_improvements', quiz_id=quiz_id))
        
        return render_template('admin/edit_improvement.html', quiz=quiz, improvement=improvement)
    
    # Admin delete improvement area
    @app.route('/admin/quizzes/<int:quiz_id>/improvements/<int:improvement_id>/delete', methods=['POST'])
    @admin_required
    def admin_delete_improvement(quiz_id, improvement_id):
        improvement = Improvement.query.get_or_404(improvement_id)
        
        if improvement.quiz_id != quiz_id:
            flash('Improvement area does not belong to this quiz', 'danger')
            return redirect(url_for('admin_improvements', quiz_id=quiz_id))
        
        db.session.delete(improvement)
        db.session.commit()
        
        flash('Improvement area has been deleted!', 'success')
        return redirect(url_for('admin_improvements', quiz_id=quiz_id))
    
    # Admin view results
    @app.route('/admin/results')
    @admin_required
    def admin_results():
        results = Result.query.order_by(Result.completed_at.desc()).all()
        return render_template('admin/results.html', results=results)
    
    # Admin view specific result
    @app.route('/admin/results/<int:result_id>')
    @admin_required
    def admin_view_result(result_id):
        result = Result.query.get_or_404(result_id)
        answers = Answer.query.filter_by(result_id=result_id).all()
        
        return render_template('admin/view_result.html', result=result, answers=answers)
    
    # Admin manage certification types
    @app.route('/admin/certifications')
    @admin_required
    def admin_certifications():
        certifications = CertificationType.query.all()
        return render_template('admin/certifications.html', certifications=certifications)
    
    # Admin add certification type
    @app.route('/admin/certifications/add', methods=['GET', 'POST'])
    @admin_required
    def admin_add_certification():
        if request.method == 'POST':
            code = request.form.get('code')
            name = request.form.get('name')
            description = request.form.get('description')
            
            # Check if certification code already exists
            existing_cert = CertificationType.query.filter_by(code=code).first()
            if existing_cert:
                flash(f'Certification code "{code}" already exists!', 'danger')
                return redirect(url_for('admin_add_certification'))
            
            certification = CertificationType(
                code=code,
                name=name,
                description=description
            )
            
            db.session.add(certification)
            db.session.commit()
            
            flash(f'Certification type "{name}" has been added!', 'success')
            return redirect(url_for('admin_certifications'))
        
        return render_template('admin/add_certification.html')
    
    # Admin edit certification type
    @app.route('/admin/certifications/<int:certification_id>/edit', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_certification(certification_id):
        certification = CertificationType.query.get_or_404(certification_id)
        
        if request.method == 'POST':
            code = request.form.get('code')
            name = request.form.get('name')
            description = request.form.get('description')
            
            # Check if certification code already exists (for another certification)
            existing_cert = CertificationType.query.filter_by(code=code).first()
            if existing_cert and existing_cert.id != certification_id:
                flash(f'Certification code "{code}" already exists!', 'danger')
                return redirect(url_for('admin_edit_certification', certification_id=certification_id))
            
            certification.code = code
            certification.name = name
            certification.description = description
            
            db.session.commit()
            flash('Certification type has been updated!', 'success')
            return redirect(url_for('admin_certifications'))
        
        return render_template('admin/edit_certification.html', certification=certification)
    
    # Admin delete certification type
    @app.route('/admin/certifications/<int:certification_id>/delete', methods=['POST'])
    @admin_required
    def admin_delete_certification(certification_id):
        certification = CertificationType.query.get_or_404(certification_id)
        
        # Check if certification is linked to any quizzes
        linked_quizzes = Quiz.query.filter_by(certification_id=certification_id).first()
        if linked_quizzes:
            flash('Cannot delete certification type that is linked to quizzes!', 'danger')
            return redirect(url_for('admin_certifications'))
        
        db.session.delete(certification)
        db.session.commit()
        
        flash(f'Certification type "{certification.name}" has been deleted!', 'success')
        return redirect(url_for('admin_certifications'))
    
    # Guest login/register
    @app.route('/guest/login', methods=['GET', 'POST'])
    @retry_db_operation
    def guest_login():
        # Redirect to guest quizzes if already logged in as guest
        if 'guest_id' in session:
            return redirect(url_for('guest_quizzes'))
            
        # If user is logged in as admin, log them out first
        if 'admin_id' in session:
            session.pop('admin_id', None)
            flash('You have been logged out as admin to proceed as guest', 'info')
            
        if request.method == 'POST':
            name = request.form.get('name')
            mobile = request.form.get('mobile')
            email = request.form.get('email')
            certification_id = request.form.get('certification')
            
            # Simple validation
            if not name or not mobile or not certification_id:
                flash('Please fill in all required fields', 'danger')
                certifications = CertificationType.query.all()
                return render_template('guest/login.html', certifications=certifications)
            
            # Check if guest exists
            guest = Guest.query.filter_by(mobile=mobile).first()
            
            if not guest:
                # Create new guest
                guest = Guest(
                    name=name,
                    mobile=mobile,
                    email=email
                )
                db.session.add(guest)
                db.session.commit()
            
            # Log in the guest
            session['guest_id'] = guest.id
            
            # Store the selected certification
            if certification_id:
                session['selected_certification_id'] = int(certification_id)
                
            flash(f'Welcome, {guest.name}!', 'success')
            return redirect(url_for('guest_quizzes'))
        
        # Get all available certification types
        certifications = CertificationType.query.all()
        
        return render_template('guest/login.html', certifications=certifications)
    
    # Guest logout
    @app.route('/guest/logout')
    def guest_logout():
        session.pop('guest_id', None)
        flash('You have been logged out', 'success')
        return redirect(url_for('index'))
    
    # Guest quizzes page
    @app.route('/guest/quizzes')
    @guest_required
    @retry_db_operation
    def guest_quizzes():
        guest_id = session.get('guest_id')
        guest = Guest.query.get(guest_id)
        
        # Get the selected certification from session
        certification_id = session.get('selected_certification_id')
        
        if certification_id:
            # Filter quizzes by certification_id
            quizzes = Quiz.query.filter_by(is_active=True, certification_id=certification_id).all()
            certification = CertificationType.query.get(certification_id)
        else:
            # If no certification selected, show all quizzes (fallback)
            quizzes = Quiz.query.filter_by(is_active=True).all()
            certification = None
        
        # Get completed quizzes for this guest
        completed_quiz_ids = [r.quiz_id for r in Result.query.filter_by(guest_id=guest_id).filter(Result.completed_at.isnot(None)).all()]
        
        return render_template('guest/quizzes.html', 
                              quizzes=quizzes, 
                              guest=guest, 
                              certification=certification,
                              completed_quiz_ids=completed_quiz_ids)
    
    # Guest start quiz
    @app.route('/guest/quizzes/<int:quiz_id>/start')
    @guest_required
    @retry_db_operation
    def guest_start_quiz(quiz_id):
        quiz = Quiz.query.get_or_404(quiz_id)
        guest_id = session.get('guest_id')
        
        # Check if quiz is active
        if not quiz.is_active:
            flash('This quiz is not currently available', 'warning')
            return redirect(url_for('guest_quizzes'))
        
        # Check if the guest has any unfinished attempts
        existing_result = Result.query.filter_by(
            guest_id=guest_id,
            quiz_id=quiz_id,
            completed_at=None
        ).first()
        
        if existing_result:
            return redirect(url_for('guest_take_quiz', result_id=existing_result.id))
        
        # Create a new result
        questions = Question.query.filter_by(quiz_id=quiz_id).all()
        
        if not questions:
            flash('This quiz has no questions', 'warning')
            return redirect(url_for('guest_quizzes'))
        
        result = Result(
            guest_id=guest_id,
            quiz_id=quiz_id,
            total_questions=len(questions),
            started_at=datetime.utcnow()
        )
        
        db.session.add(result)
        db.session.commit()
        
        return redirect(url_for('guest_take_quiz', result_id=result.id))
    
    # Guest take quiz
    @app.route('/guest/quizzes/take/<int:result_id>', methods=['GET', 'POST'])
    @guest_required
    @retry_db_operation
    def guest_take_quiz(result_id):
        result = Result.query.get_or_404(result_id)
        guest_id = session.get('guest_id')
        
        # Security check
        if result.guest_id != guest_id:
            flash('You do not have access to this quiz', 'danger')
            return redirect(url_for('guest_quizzes'))
        
        # Check if already completed
        if result.completed_at:
            return redirect(url_for('guest_result', result_id=result.id))
        
        quiz = Quiz.query.get(result.quiz_id)
        
        # Get all questions for this quiz
        questions = Question.query.filter_by(quiz_id=quiz.id).all()
        
        # Get answered question IDs
        answered_question_ids = [a.question_id for a in Answer.query.filter_by(result_id=result.id).all()]
        
        # Get unanswered questions
        unanswered_questions = [q for q in questions if q.id not in answered_question_ids]
        
        # If all questions answered or form submitted with final_submit, complete the quiz
        if request.method == 'POST' and request.form.get('final_submit') or not unanswered_questions:
            # Calculate score and complete the quiz
            result.completed_at = datetime.utcnow()
            result.time_taken = int((result.completed_at - result.started_at).total_seconds())
            
            correct_answers = Answer.query.filter_by(result_id=result.id, is_correct=True).count()
            result.score = correct_answers
            result.percentage = (correct_answers / result.total_questions) * 100
            result.passed = result.percentage >= quiz.pass_percentage
            
            # Suggest improvement areas
            if not result.passed:
                # Get all possible improvements for this quiz
                all_improvements = Improvement.query.filter_by(quiz_id=quiz.id).all()
                
                # Select up to 3 random improvements
                selected_improvements = random.sample(all_improvements, min(3, len(all_improvements)))
                
                for improvement in selected_improvements:
                    suggested = SuggestedImprovement(
                        result_id=result.id,
                        improvement_id=improvement.id
                    )
                    db.session.add(suggested)
            
            db.session.commit()
            return redirect(url_for('guest_result', result_id=result.id))
        
        if request.method == 'POST':
            # Process the answer
            question_id = int(request.form.get('question_id'))
            selected_option_id = int(request.form.get('option'))
            
            # Get the option to check if it's correct
            selected_option = Option.query.get(selected_option_id)
            
            # Record the answer
            answer = Answer(
                result_id=result.id,
                question_id=question_id,
                selected_option_id=selected_option_id,
                is_correct=selected_option.is_correct
            )
            
            db.session.add(answer)
            db.session.commit()
            
            # Get the next unanswered question
            return redirect(url_for('guest_take_quiz', result_id=result.id))
        
        # If there are no more questions, prompt to submit
        if not unanswered_questions:
            return render_template('guest/submit_quiz.html', 
                                  quiz=quiz, 
                                  result=result,
                                  answered_count=len(answered_question_ids),
                                  total_questions=len(questions))
        
        # Get the next question
        current_question = unanswered_questions[0]
        options = Option.query.filter_by(question_id=current_question.id).all()
        
        # Calculate progress
        progress = {
            'current': len(answered_question_ids) + 1,
            'total': len(questions),
            'percentage': int((len(answered_question_ids) / len(questions)) * 100)
        }
        
        # Calculate remaining time if there's a time limit
        time_limit_seconds = None
        if quiz.time_limit:
            time_limit_seconds = quiz.time_limit * 60
            elapsed = (datetime.utcnow() - result.started_at).total_seconds()
            remaining = time_limit_seconds - elapsed
            
            if remaining <= 0:
                # Time's up - automatically complete the quiz
                return redirect(url_for('guest_take_quiz', result_id=result.id))
            
            progress['time_remaining'] = int(remaining)
        
        return render_template('guest/take_quiz.html', 
                              quiz=quiz, 
                              question=current_question, 
                              options=options, 
                              progress=progress,
                              result=result,
                              time_limit_seconds=time_limit_seconds)
    
    # Guest view quiz result
    @app.route('/guest/results/<int:result_id>')
    @guest_required
    @retry_db_operation
    def guest_result(result_id):
        result = Result.query.get_or_404(result_id)
        guest_id = session.get('guest_id')
        
        # Security check
        if result.guest_id != guest_id:
            flash('You do not have access to this result', 'danger')
            return redirect(url_for('guest_quizzes'))
        
        # If quiz is not completed yet
        if not result.completed_at:
            return redirect(url_for('guest_take_quiz', result_id=result.id))
        
        quiz = Quiz.query.get(result.quiz_id)
        answers = Answer.query.filter_by(result_id=result.id).all()
        
        # Get suggested improvements
        suggested_improvements = SuggestedImprovement.query.filter_by(result_id=result.id).all()
        
        return render_template('guest/result.html', 
                              result=result, 
                              quiz=quiz, 
                              answers=answers,
                              suggested_improvements=suggested_improvements)
    
    # Guest view all results
    @app.route('/guest/results')
    @guest_required
    @retry_db_operation
    def guest_results():
        guest_id = session.get('guest_id')
        results = Result.query.filter_by(guest_id=guest_id).order_by(Result.completed_at.desc()).all()
        
        return render_template('guest/results.html', results=results)
    
    # Error pages
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500
