import win32com.client as win32
from src.config.logging_config import Logger
from src.data_manager.meal import get_recent_meals_string_for_user
from src.data_manager.user import get_all_users
from src.db_session import session_scope
from src.utils.localization_utils import get_localized_string
from src.utils.email_utils import get_users_adresses
import os
import shutil
import tempfile

logger = Logger('myfoodrepo.email_manager').get_logger()


def send_all_study_end_mails(app):
    """
    Sends all "first" study-ending mails (feedback survey) to users in our cohort. Functions only with Windows + Outlook 2016+ installed.

    Args:
     - app: The Flask application.
    """
    outlook = win32.Dispatch('outlook.application')
    
    with app.app_context():
        users = get_all_users()
        users_adresses = get_users_adresses()

    for user in users :
        if not user.last_meal_log:
            logger.warning(f"No activity for user {user.id}, not sending an e-mail")
            continue
        else:
            email_row = users_adresses[users_adresses['Phone Number'] == user.phone_number]

            if email_row.empty:
                logger.warning(f"No email found for phone number: {user.phone_number}")
                continue

            email = email_row['E-mail Address'].values[0]
            send_study_end_mail(user,outlook,email,app)



def send_study_end_mail(user, outlook, adress ,app):
    """
    Sends a study ending (feedback survey) e-mail to a specific user in the cohort.

    Args:
       - user: The User to send the e-mail to.
       - outlook: The Outlook instance through e-mail should be sent.
       - adress: The user e-mail adress
       - app: The Flask application
    """
    mail = outlook.CreateItem(0)
    mail.To = adress
    with app.app_context():
        mail.Subject = get_localized_string("ending-mail-subject", user.language)
        mail.HTMLBody = get_localized_string("ending-mail-html-body", user.language)
    mail.Send()
    logger.debug(f"Email sent to: {adress}")


def send_study_report_mail(user, outlook, adress ,app):
    """
    Sends the final e-mail (containing the nutritional report) to a specific user in the cohort.

    Args:
       - user: The User to send the e-mail to.
       - outlook: The Outlook instance through e-mail should be sent.
       - adress: The user e-mail adress
       - app: The Flask application
    """

    mail = outlook.CreateItem(0)
    mail.To = adress
    curr_directory = os.path.abspath(os.path.dirname(__file__))
    project_directory = os.path.join(curr_directory, '..', '..')
    output_directory = os.path.join(project_directory, 'output')
    original_file_path  = os.path.join(output_directory,f"{user.id}_nutrition_report.pdf")

    with app.app_context():
        with tempfile.TemporaryDirectory() as tmpdirname:
            desired_filename = get_localized_string("report-name", user.language)
            temp_file_path = os.path.join(tmpdirname, desired_filename)
            shutil.copyfile(original_file_path, temp_file_path)

    
            mail.Subject = get_localized_string("report-mail-subject", user.language)
            mail.HTMLBody = get_localized_string("report-mail-html-body", user.language)
            mail.Attachments.Add(temp_file_path)

    mail.Send()
    logger.debug(f"Email sent to: {adress} with attachment renamed to {desired_filename}")
