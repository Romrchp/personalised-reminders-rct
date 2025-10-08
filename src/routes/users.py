from flask import Blueprint, jsonify, render_template, request, flash, redirect, url_for
from io import StringIO
from flask import make_response
import pandas as pd
from src.data_manager.myfoodrepo_data_manager import healthy_index_preprocessing
from src.data_manager.user import get_all_users, get_users_by_study_group, get_age_distribution, get_gender_distribution, get_language_distribution, get_user,checking_users_sanity, update_user_participation, get_started_users_per_group, update_user_study_end
from src.data_manager.health_summary.health_summary import generate_health_summary
from src.communication.conversation_starter import start_specific_conversation
from src.communication.conversation_ender import end_specific_conversation
from src.config.logging_config import Logger
from src.utils.csv_utils import users_to_dataframe
from typing import Union
import json

from src.utils.auth_utils import login_required

users_bp = Blueprint('users', __name__)
logger = Logger('myfoodrepo.webapp').get_logger()



# ========== Home Endpoints ==========
@users_bp.route('/',methods=['GET','POST'])
def users():
    search = request.args.get('search', '')
    gender = request.args.get('gender', '')
    language = request.args.get('language', '')
    page = request.args.get('page', 1, type=int)
    users_per_group = [get_users_by_study_group(i) for i in range(4)]

    users_data = get_all_users()
    sanity_check_results = checking_users_sanity()

    group_data = {
        '0': {
            'name': 'Group 0',
            'description': 'No reminders, no communication',
            'icons': ['fas fa-bell-slash', 'fas fa-comment-slash'],
            'count': len(users_per_group[0]) if len(users_per_group) > 0 else 0
        },
        '1': {
            'name': 'Group 1',
            'description': 'Generic reminders only',
            'icons': ['fas fa-bell', 'fas fa-comment-slash'],
            'count': len(users_per_group[1]) if len(users_per_group) > 1 else 0
        },
        '2': {
            'name': 'Group 2',
            'description': 'Chatbot communication only',
            'icons': ['fas fa-bell-slash', 'fas fa-comment-dots'],
            'count': len(users_per_group[2]) if len(users_per_group) > 2 else 0
        },
        '3': {
            'name': 'Group 3',
            'description': 'Personalized reminders & communication',
            'icons': ['fas fa-bell', 'fas fa-comment-dots'],
            'count': len(users_per_group[3]) if len(users_per_group) > 3 else 0
        }
    }



    return render_template('users.html',
                            users=users_data,
                            total_users=len(users_data),
                            users_per_group=users_per_group,
                            sanity_check_results=sanity_check_results,
                            group_data_json=json.dumps(group_data))


# ========== Managing users Endpoints ==========

@users_bp.route("/edit/<int:user_id>", methods=['GET', 'POST'])
def edit_user(user_id):
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        curr_user = get_user(phone_number)
        return render_template("users/edit_user.html", user=curr_user)
    
    return "This route expects a POST request with phone number.", 400


@users_bp.route("/add_user", methods=['GET','POST'])
def add():
    logger.debug("Adding a user")
    phone_number: Union[str, None] = request.values.get('phone_number', None)
    logger.info(f"Phone number of the user: {phone_number}")
    phone_number = "+33647873573"
    if phone_number is None:
        return "Phone number is None"

    if phone_number.startswith('00'):
        phone_number = '+' + phone_number[2:]

    key = request.values.get('participation_key', None)
    return render_template('add_user.html')

@users_bp.route("/delete_user", methods=['GET','POST'])
def delete():
    return(render_template('delete_user.html'))


@users_bp.route("/update_user_participation/<int:user_id>", methods=['POST'])
def update_participation(user_id):
    phone_nb = request.form.get('phone_number')
    new_withdrawal_status = request.form.get('withdrawal') == 'True'
    update_user_participation(phone_nb,new_withdrawal_status)
    flash(f"✅New participation status for user {user_id} is {new_withdrawal_status}", "success")
    return redirect(url_for('users.manage_users'))


@users_bp.route("/update_user_ending/<int:user_id>", methods=['POST'])
def update_ending(user_id):
    phone_nb = request.form.get('phone_number')
    new_ending_status = request.form.get('ending') == 'True'
    update_user_study_end(phone_nb,new_ending_status)
    flash(f"✅New participation status for user {user_id} is {new_ending_status}", "success")
    return redirect(url_for('users.manage_users'))


@users_bp.route("/generate_health_summaries", methods = ['GET', 'POST'])
def generate_health_summaries():
    all_users = get_all_users()
    for user in all_users :
        user_food_recap = healthy_index_preprocessing(user)
        generate_health_summary(user.id,user.phone_number,user.myfoodrepo_key,user.diet_goal,user.language,user_food_recap)
        figure_path = f"output/figures/{user.id}_nutrition_dashboard.png"
        output_pdf_path = f"output/{user.id}_nutrition_report.pdf"
    
    flash(f"✅ Generated all users health summaries", "success")
    return redirect(url_for('users.manage_users'))

@users_bp.route("/download-users", methods=["GET"])
@login_required
def download_users_csv():
    try:
        users = get_all_users()

        if len(users) == 0:
            flash("No users available for download.", "warning")
            return redirect(url_for("users.users"))
        
        users = users_to_dataframe(users)
        df = pd.DataFrame(users)

        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        response = make_response(csv_buffer.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=users_backup.csv"
        response.headers["Content-Type"] = "text/csv"
        return response

    except Exception as e:
        logger.error(f"Error while exporting messages: {e}")
        flash("An error occurred while trying to download the users.", "danger")
        return redirect(url_for("users.users"))



@users_bp.route("/manage_users", methods=['GET','POST'])
def manage_users():
    all_users = get_all_users()
    return(render_template("users/manage_users.html", all_users = all_users))

@users_bp.route("start_conv/<int:user_id>", methods = ['POST']) 
def start_specific_conv(user_id):
    phone_nb = request.form.get('phone_number')
    curr_user = get_user(phone_nb)
    start_specific_conversation(curr_user)
    flash(f"✅ Conversation started with user {user_id}", "success")
    return redirect(url_for('users.manage_users'))

@users_bp.route("end_conv/<int:user_id>", methods = ['POST']) 
def end_specific_conv(user_id):
    phone_nb = request.form.get('phone_number')
    curr_user = get_user(phone_nb)
    end_specific_conversation(curr_user)
    flash(f"✅ Conversation ended with user {user_id}", "success")
    return redirect(url_for('users.manage_users'))



# ========== Graph & Data Related Endpoints ==========

@users_bp.route('/gender-distrib', methods=['GET'])
def users_genders():
    study_group = request.args.get('study_group', default=None, type=int)
    genders = get_gender_distribution(study_group)
    return jsonify(genders)

@users_bp.route('/age-distrib', methods=['GET'])
def users_ages():
    study_group = request.args.get('study_group', default=None, type=int)
    ages = get_age_distribution(study_group)
    return jsonify(ages)

@users_bp.route('/language-distrib', methods=['GET'])
def users_languages():
    study_group = request.args.get('study_group', default=None, type=int)
    languages = get_language_distribution(study_group)
    return jsonify(languages)

@users_bp.route('/active-inactive-users', methods = ['GET'])
def started_users():
    active_inactive_users = get_started_users_per_group()
    return(jsonify(active_inactive_users))


@users_bp.route("/get_users", methods=['GET', 'POST'])
def get_users():
    logger.debug("Fetching all users")
    users = get_all_users()
    return [user.to_dict() for user in users]
