import dotenv
dotenv.load_dotenv()

from flask import Flask, request, redirect, url_for, session
from src.config.config import create_app
from src.routes import register_blueprints


app = create_app()

# Store app as a global variable to be used in other modules
app.app_config = {
    'is_production': True  # Set to True in production environment
}

register_blueprints(app)


@app.before_request
def restrict_access():
    allowed_routes = ['main.login', 'messages.sms_reply', 'static'] 
    if request.endpoint not in allowed_routes and not session.get("authenticated"):
        return redirect(url_for("main.login"))


if __name__ == "__main__":
    # Make sure app is available to all modules
    with app.app_context():
        app.run(debug=False, host='0.0.0.0', port=8062, use_reloader=False)