from locale import currency
from flask import Blueprint, render_template, jsonify, url_for, flash, redirect,request
from io import StringIO
from flask import make_response
import pandas as pd
from src.data_manager.meal import edit_meal_characteristic, get_all_meals, get_meal_by_id, get_recent_meals_string_for_user, get_cohort_retention, get_meal_logging_frequency, get_meals_per_study_group, get_meals_per_day_per_study_group, get_meal_by_id, remove_user_meal, checking_meals_sanity, get_meal_logging_by_hour
from src.data_manager.myfoodrepo_data_manager import update_database
from src.utils.auth_utils import login_required
from src.config.logging_config import Logger
from src.utils.csv_utils import meals_to_dataframe

meals_bp = Blueprint('meals', __name__)
logger = Logger('meals_routes').get_logger()

# ========== Home Endpoints ==========

@meals_bp.route("/", methods=['GET', 'POST'])
def home():

    meals_per_study_group = get_meals_per_study_group()
    all_meals = get_all_meals(True)[:20]
    sanity_check_results = checking_meals_sanity()
    return render_template(
        "meals.html", 
        meals = all_meals, 
        meals_per_study_group = meals_per_study_group,
        meal_sanity_check_results=sanity_check_results)

@meals_bp.route("/recent", methods=['GET'])
def recent_meals():
    meals = get_recent_meals_string_for_user("+33647873573")
    print(f"meals are: {meals}")
    return "MEALS"

# ========== Meals Syncing route ==========

@meals_bp.route("/sync_meals_data", methods=['GET', 'POST'])
def sync_meals_data():
    full_sync = request.args.get('full_sync', 'false').lower() == 'true'
    logger.info(f"Manual syncing of the Meals data - Full sync: {full_sync}")
    update_database(full_sync=full_sync)
    flash("✅ Meals correctly updated.", "success")
    return redirect(url_for('meals.home'))


# ========== Meals Management & Editing Endpoints ==========

@meals_bp.route("/remove_meal/<int:meal_id>", methods=['POST'])
def remove_meal(meal_id):
    msg, status = remove_user_meal(meal_id)
    all_meals = get_all_meals()
    return render_template("meals/manage_meals.html", all_meals=all_meals)

@meals_bp.app_context_processor
def meal_utility_processor():
    def edit_meal_url(meal):
        return url_for('meals.edit_meal', meal_id=meal.id)
    return dict(edit_meal_url=edit_meal_url)

@meals_bp.route("/edit/<int:meal_id>", methods=['GET', 'POST'])
def edit_meal(meal_id):
    curr_meal = get_meal_by_id(meal_id)
    return render_template("meals/edit_meal.html", meal=curr_meal)


@meals_bp.route("/update_meal/<int:meal_id>", methods=["POST"])
def update_meal(meal_id):
    msg = edit_meal_characteristic(meal_id)
    
    if msg == "Information updated" : 
        flash("Meal updated successfully", "success")
    else: 
        flash("Does not work :(", "danger")

    flash("Meal updated successfully", "success")
    return redirect(url_for("meals.edit_meal", meal_id=meal_id))

@meals_bp.route("/manage_meals", methods=["GET","POST"])
def manage_meals():
    all_meals = get_all_meals()
    return(render_template("meals/manage_meals.html", all_meals = all_meals))

@meals_bp.route("/download-meals", methods=["GET"])
@login_required
def download_meals_csv():
    try:
        meals = get_all_meals(datetime_sort=False)

        if len(meals) == 0:
            flash("No users available for download.", "warning")
            return redirect(url_for("meals.home"))
        
        meals = meals_to_dataframe(meals)
        df = pd.DataFrame(meals)

        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        response = make_response(csv_buffer.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=meals_backup.csv"
        response.headers["Content-Type"] = "text/csv"
        return response

    except Exception as e:
        logger.error(f"Error while exporting messages: {e}")
        flash("An error occurred while trying to download the users.", "danger")
        return redirect(url_for("users.users"))


# ========== Graph & Data Related Endpoints ==========

@meals_bp.route("/cohort_retention", methods=['GET'])
def cohort_retention():
    
    retention_data = get_cohort_retention()
    result = [{"date": str(date), "user_count": len(users)} for date, users in retention_data.items()]
    return jsonify(result)


@meals_bp.route("/logging_frequency", methods=['GET'])
def logging_frequency():

    meal_data = get_meal_logging_frequency()
    result = [{"date": str(date), "meal_count": sum(count for count in user_meals.values())} 
              for date, user_meals in meal_data.items()]
    return jsonify(result)

@meals_bp.route("/meal_retention_by_hour", methods=['GET'])
def meal_retention_by_hour():
    """
    API endpoint that returns meal logging frequency data by hour of day.
    
    Returns:
        JSON: List of dictionaries containing hour and meal_count for each hour (0-23)
    """
    hourly_data = get_meal_logging_by_hour()
    
    retention_data = []
    for hour in range(24):
        hour_label = f"{hour:02d}:00"
        meal_count = hourly_data.get(hour, 0)
        
        retention_data.append({
            "hour": hour_label,
            "hour_numeric": hour,
            "meal_count": meal_count
        })
    
    return jsonify(retention_data)

@meals_bp.route("/meals_per_day", methods=['GET'])
def meals_per_day():
    meals_data = get_meals_per_day_per_study_group()
    
    result = []
    for study_group, daily_meals in meals_data.items():
        for entry in daily_meals:
            result.append({
                "study_group": study_group,
                "date": entry["date"],
                "meal_count": entry["meal_count"]
            })
    
    return jsonify(result)



