from flask import Flask, render_template, redirect, url_for, request, session, flash

from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash, check_password_hash

import os

db = SQLAlchemy()

# Define models globally (SQLAlchemy requires this before initializing db with app)

class Admin(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(80), unique=True, nullable=False)

    password = db.Column(db.String(200), nullable=False)

def create_app():

    app = Flask(__name__)

    app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey")

    # Configure PostgreSQL or fallback to SQLite

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///site.db")

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Register function after app and db are fully initialized

    @app.before_request

    def create_initial_admin():

        with app.app_context():

            db.create_all()

            if not Admin.query.filter_by(username='admin').first():

                hashed_password = generate_password_hash('admin123', method='sha256')

                admin = Admin(username='admin', password=hashed_password)

                db.session.add(admin)

                db.session.commit()

    @app.route('/')

    def home():

        return "Flask app running on Render successfully!"

    return app

# Expose app for Gunicorn

app = create_app()

if __name__ == '__main__':

    app.run(debug=True)
 
