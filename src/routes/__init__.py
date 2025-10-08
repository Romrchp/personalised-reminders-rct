from flask import Blueprint

# Import all blueprints & then register them to the app.
from .main import main_bp
from .users import users_bp
from .meals import meals_bp
from .reminders import reminders_bp
from .messages import messages_bp

def register_blueprints(app):
    """Registers all blueprints to the Flask app."""
    app.register_blueprint(main_bp)
    app.register_blueprint(users_bp, url_prefix="/users")
    app.register_blueprint(meals_bp, url_prefix="/meals")
    app.register_blueprint(messages_bp, url_prefix="/messages")
    app.register_blueprint(reminders_bp, url_prefix="/reminders")

