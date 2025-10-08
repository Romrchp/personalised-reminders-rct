import os
from flask import Blueprint, render_template, session, redirect, url_for, request, flash

from src.scheduler.scheduler import get_job_execution_report
from src.communication.conversation_ender import end_conversations
from src.communication.conversation_starter import start_conversations
from src.data_manager.form_data_manager import generate_participation_keys, update_cohort_participants_info
from src.data_manager.meal import get_all_meals
from src.data_manager.message import get_all_messages, get_study_start_date
from src.data_manager.reminder import get_all_reminders
from src.data_manager.user import get_all_users
from src.init_experiment import fill_db_from_google_form_data
from src.utils.auth_utils import login_required

main_bp = Blueprint('main', __name__)
DASHBOARD_ACCESS_KEY = os.getenv("DASHBOARD_ACCESS_KEY")

# ========== Login Route ==========

@main_bp.route("/", methods=['GET', 'POST'])
def login():
    """Login page with access key authentication."""
    if request.method == 'POST':
        entered_key = request.form.get('access_key')
        if entered_key == DASHBOARD_ACCESS_KEY:
            session["authenticated"] = True
            return redirect(url_for("main.home"))
        else:
            flash("Invalid access key. Please try again.", "error")
            return redirect(url_for("main.login"))
    return render_template("login.html")

# ========== Home Route ==========

@main_bp.route("/home", methods=['GET', 'POST'])
@login_required
def home():
    """Dashboard overview with counts for various entities."""
    users_count = len(get_all_users())
    messages_count = len(get_all_messages(filter_twilio_message_id=True))
    reminders_count = len(get_all_reminders())
    meals_count = len(get_all_meals())
    study_start_date_raw = get_study_start_date()

    study_start_date_formatted = None
    if study_start_date_raw:
        from datetime import datetime
        if isinstance(study_start_date_raw, str):
            date_obj = datetime.fromisoformat(study_start_date_raw.replace('Z', '+00:00'))
        else:
            date_obj = study_start_date_raw
        study_start_date_formatted = date_obj.strftime("%B %d, %Y at %I:%M %p")

    study_active = study_start_date_raw is not None
    study_status = "Running" if study_active else "Not Started"
    study_duration = study_start_date_raw  if study_active else None

    return render_template("index.html",
                           users_count=users_count,
                           messages_count=messages_count,
                           reminders_count=reminders_count,
                           meals_count=meals_count,
                           study_start_date = study_start_date_formatted,
                           study_start_date_raw = study_start_date_raw,
                           study_active=study_active,
                           study_status=study_status,
                           study_duration=study_duration)

# ========== Data Management Routes ==========

@main_bp.route("/form", methods=['GET', 'POST'])
@login_required
def process_google_form():
    """Generate new participation keys."""
    keys = f"{generate_participation_keys(1)}"
    return keys

@main_bp.route("/init", methods=['GET', 'POST'])
@login_required
def init_data_from_google_form():
    """Populate DB from Google Form responses."""
    fill_db_from_google_form_data()
    flash(f"✅ Database initialized with participants data.", "success")
    return redirect(url_for('main.home'))

@main_bp.route("/update_cohort_info", methods=['GET', 'POST'])
@login_required
def update_cohort():
    """Update the csv file with new data from a CSV file."""
    update_cohort_participants_info()
    flash(f"✅ Database updated with the newest participants data.", "success")
    return redirect(url_for('main.home'))

@main_bp.route('/job-report')
@login_required
def job_report():
    return get_job_execution_report()


# ========== Conversation Management Routes ==========

@main_bp.route("/start", methods=['GET', 'POST'])
@login_required
def convs_start():
    """Start all conversations and scheduling."""
    start_conversations()
    flash(f"✅ Conversations have been started with all users in the database.", "success")
    return redirect(url_for('main.home'))


@main_bp.route("/stop", methods=['GET', 'POST'])
@login_required
def convs_end():
    """Stop all conversations for users for which the study is finished."""
    end_conversations()
    flash(f"✅ Conversations ended with all necessary users.","success")
    return redirect(url_for('main.home'))


# ========== Misc / Static Views ==========

@main_bp.route("/WIP", methods=['GET'])
def wip():
    """Work in progress page."""
    return render_template('WIP.html')

