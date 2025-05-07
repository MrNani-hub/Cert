from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
# Initialize extensions
db = SQLAlchemy()
# Application Factory
def create_app():
   app = Flask(__name__)
   app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey")
   # Database configuration (PostgreSQL)
   app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///site.db")
   app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
   db.init_app(app)
   # Define models inside app context
   with app.app_context():
       class Admin(db.Model):
           id = db.Column(db.Integer, primary_key=True)
           username = db.Column(db.String(80), unique=True, nullable=False)
           password = db.Column(db.String(200), nullable=False)
       db.create_all()
       # Create default admin if not exists
       @app.before_first_request
       def create_initial_admin():
           if not Admin.query.filter_by(username='admin').first():
               hashed_password = generate_password_hash('admin123', method='sha256')
               admin = Admin(username='admin', password=hashed_password)
               db.session.add(admin)
               db.session.commit()
   # Routes
   @app.route('/')
   def home():
       return "Flask app is running successfully on Render!"
   return app
# Gunicorn entry point
app = create_app()
if __name__ == '__main__':
   app.run(debug=True)
