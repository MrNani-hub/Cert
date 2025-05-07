from flask import Flask, render_template, request, redirect, url_for, session, flash

from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash, check_password_hash

import os

# Initialize SQLAlchemy globally

db = SQLAlchemy()

# Define the Admin model

class Admin(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(50), unique=True, nullable=False)

    password = db.Column(db.String(200), nullable=False)

# Function to create an initial admin user

def create_initial_admin():

    admin_exists = Admin.query.filter_by(username='admin').first()

    if not admin_exists:

        hashed_pw = generate_password_hash('admin123', method='sha256')

        new_admin = Admin(username='admin', password=hashed_pw)

        db.session.add(new_admin)

        db.session.commit()

# Factory function to create the Flask app

def create_app():

    app = Flask(__name__)

    app.secret_key = 'your_secret_key'  # Use a strong secret in production

    # Render-compatible PostgreSQL connection or local SQLite fallback

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///clinic.db')

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():

        db.create_all()

        create_initial_admin()

    # Routes

    @app.route('/')

    def home():

        return render_template('login.html')

    @app.route('/login', methods=['POST'])

    def login():

        username = request.form['username']

        password = request.form['password']

        admin = Admin.query.filter_by(username=username).first()

        if admin and check_password_hash(admin.password, password):

            session['admin'] = True

            return redirect(url_for('dashboard'))

        else:

            flash('Invalid credentials')

            return redirect(url_for('home'))

    @app.route('/dashboard')

    def dashboard():

        if 'admin' in session:

            return render_template('dashboard.html')

        else:

            return redirect(url_for('home'))

    return app

# Run locally

if __name__ == '__main__':

    app = create_app()

    app.run(host='0.0.0.0', port=5000)
 
