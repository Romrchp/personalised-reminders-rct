from flask import Blueprint, render_template, request, redirect, url_for, flash,current_app
from src.data_manager.reminder import add_reminder, add_reminder_all_users, get_all_reminders, get_study_group_reminders, reminders_check, remove_reminder, checking_reminders_sanity
from src.scheduler.scheduler import get_all_running_jobs, unschedule_job, schedule_reminder, schedule_reminders
from src.config.logging_config import Logger



reminders_bp = Blueprint('reminders', __name__)
logger = Logger('reminders_routes').get_logger()


# ========== Reminders home page ==========

@reminders_bp.route("/", methods= ["GET","POST"])
def landing():

    missing_reminders_dic = reminders_check()
    reminders_per_group = [get_study_group_reminders(i) for i in range(4)]
    sanity_check_results = checking_reminders_sanity()

    return render_template(
        "reminders.html",
        missing_reminders_dic=missing_reminders_dic,
        sanity_check_results=sanity_check_results,
        reminders_per_group=reminders_per_group
    )
    

# ========== Reminders overview & Management - Endpoints ==========

@reminders_bp.route("/manage_reminders", methods= ["GET","POST"])
def manage_reminders():
    all_reminders = get_all_reminders()
    return render_template("reminders/manage_reminders.html", all_reminders=all_reminders)
    
@reminders_bp.route("/add_reminder", methods= ["POST"])
def add_user_reminder() :
    user_id = request.form.get("user_id")
    time = request.form.get("time")
    meal_type = request.form.get("meal_type")
    return add_reminder(user_id,time,meal_type)
    

@reminders_bp.route("/remove_reminder/<int:reminder_id>", methods=["POST"])
def remove_user_reminder(reminder_id) :
    return remove_reminder(reminder_id)

@reminders_bp.route("/add_all", methods=['GET','POST'])
def add_all_reminders():
    logger.info("Adding reminders for all users")
    add_reminder_all_users()
    flash("✅ All reminders were successfully added.", "success")
    return redirect(url_for('reminders.landing'))

    
# ========== Reminders Scheduling - Endpoints ==========

@reminders_bp.route("/unschedule_job/<string:job_id>", methods=["POST"])
def unschedule_reminder_job(job_id):
    msg,status = unschedule_job(job_id)
    if status == 200 :
        flash(f"Job n°{job_id} unscheduled successfully.","success")
    elif status == 400:
        flash(f"Failed to unschedule job n°{job_id}", "danger")
    else:
        flash(f"Something unexpected happen. Please refer to the log file for more info.", "danger")

    return(redirect(url_for('reminders.manage_jobs')))

@reminders_bp.route("/schedule_job", methods=["POST"])
def schedule_reminder_job():
    user_id = request.form.get("user_id")
    reminder_id = request.form.get("reminder_id")
    meal_type = request.form.get("meal_type")

    status = schedule_reminder(user_id,reminder_id,meal_type,current_app)
    if status == 200 :
        flash(f"Reminder job scheduled for user {user_id}.", "success")
    else:
        flash("Invalid user or reminder ID.", "danger")
    return redirect(url_for('reminders.manage_jobs'))

@reminders_bp.route("/schedule_all", methods=['GET','POST'])
def schedule_all_reminders():
    logger.info("Scheduling reminders for all users")
    schedule_reminders(current_app)
    flash("✅ All reminders were successfully scheduled.", "success")
    return redirect(url_for('reminders.landing'))

@reminders_bp.route("/manage_jobs", methods=["GET"])
def manage_jobs():
    jobs = get_all_running_jobs()
    return render_template("reminders/manage_scheduling.html", jobs=jobs) 


