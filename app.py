from flask import Flask, render_template, redirect, url_for, request, flash

from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash, check_password_hash

import os

# Initialize Flask app

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key")

# Render-compatible PostgreSQL URL (environment variable recommended)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(

    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/mydb"

)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy

db = SQLAlchemy(app)

# Define Admin model

class Admin(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(80), unique=True, nullable=False)

    password = db.Column(db.String(200), nullable=False)

# Create tables before the first request

@app.before_request

def create_tables_and_admin():

    db.create_all()

    if not Admin.query.filter_by(username='admin').first():

        hashed_pw = generate_password_hash('admin123', method='pbkdf2:sha256')

        admin = Admin(username='admin', password=hashed_pw)

        db.session.add(admin)

        db.session.commit()

        print("Default admin user created")

# Example route

@app.route('/')

def index():

    return "Welcome to the Flask App!"

# Example admin login route

@app.route('/login', methods=['GET', 'POST'])

def login():

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        admin = Admin.query.filter_by(username=username).first()

        if admin and check_password_hash(admin.password, password):

            return f"Welcome, {admin.username}!"

        else:

            flash("Invalid credentials")

    return render_template('login.html')  # Ensure you have login.html in /templates

# Run the app locally (use gunicorn in production)

if __name__ == '__main__':

    app.run(debug=True)
 
