from flask import Blueprint, current_app, request, render_template, redirect, url_for, flash, current_app,jsonify, Response
from twilio.twiml.messaging_response import MessagingResponse
import threading
import pandas as pd
from io import StringIO
from flask import make_response
from src.data_manager.message import get_messages_count_per_day_per_study_group, get_study_group_messages, get_messages_count_per_day ,get_user_messages_per_hour, get_all_messages, checking_message_sanity
from src.utils.message_utils import convert_from_whatsapp_number_format
from src.response.response_manager import process_openai_response, send_interim_response
from src.communication.twilio_tool import NewTwilioConversationManager
from src.communication.messaging_service import SMSService
from src.data_manager.user import detect_user_participation_change, is_user_registered, is_user_allowed_to_chat, update_user_participation
from src.config.logging_config import Logger
from src.utils.csv_utils import messages_to_dataframe

from src.utils.auth_utils import login_required

messages_bp = Blueprint('messages', __name__)
logger = Logger('messages_routes').get_logger()
opt_out_keywords = ['cancel','end','quit','stop','stopall','studystop','unsubscribe']
opt_in_keywords = ['start','studystart','unstop','yes']

# ========== Home Page ==========

@messages_bp.route("/", methods=['GET','POST'])
def messages_home():
        
        messages_per_group = [get_study_group_messages(i) for i in range(4)]
        messages_count = get_messages_count_per_day()
        sanity_check_results = checking_message_sanity()

        return render_template('messages.html',
                                messages_per_group = messages_per_group, 
                                messages_count = messages_count,
                                sanity_check_results = sanity_check_results)

# ========== Managing Messages Endpoint ==========

@messages_bp.route("/manage_messages", methods=["GET","POST"])
def manage_messages():
    all_messages = get_all_messages(filter_assistant_messages=True)
    return(render_template("messages/manage_messages.html", all_messages = all_messages))


# ========== Graph & Data Related Endpoints ==========

@messages_bp.route("/stats", methods=['GET'])
def messages_stats():
    messages_count = get_messages_count_per_day()
    return jsonify(messages_count)

@messages_bp.route("/per-hour", methods=['GET'])
def messages_per_hour():
     messages_per_hour = get_user_messages_per_hour()
     return jsonify(messages_per_hour)

@messages_bp.route("/per-day-and-study-group", methods=['GET'])
def per_day_and_study_group():
     messages = get_messages_count_per_day_per_study_group()
     formatted_messages = {
        "study_groups": messages
    }
     return jsonify(formatted_messages)


# ========== Messages response & sending Endpoints ========== 

@messages_bp.route("/sms/", methods=['POST'])
def sms_reply():
    logger.info(f"Received SMS request from {request.remote_addr} with data: {request.form}")
    body = request.values.get('Body', None)
    from_number = convert_from_whatsapp_number_format(request.values.get('From', None))
    twilio_message_id = request.values.get('MessageSid', None)

    if not is_user_registered(from_number): 
        logger.warning(f"Receiving messages from an unregistered phone number: {from_number}")
        return Response(status=204)
    
    is_allowed, reason = is_user_allowed_to_chat(from_number)


    if not is_allowed and reason == "User is not in an allowed study group" and body.lower() not in [word.lower() for word in opt_out_keywords]  :
        logger.warning(f"Receiving unexpected messages from: {from_number}, which is not allowed to chat.")
        return Response(status=204)
    
    
    elif not is_allowed and reason == "User has withdrawn" and body.lower() not in [word.lower() for word in opt_in_keywords] :
         logger.warning(f"Receiving messages from a withdrawn user : {from_number}")
         return Response(status=204)
    
    if not is_allowed and reason == "Study has ended for the user" and body.lower() not in [word.lower() for word in opt_out_keywords]  :
        logger.warning(f"Receiving messages from: {from_number}, for which the study is over.")
        return Response(status=204)

    else:

        logger.info(f"💬 Received a message from: {from_number} with content: {body}")
        changing_participation_state, withdrawal = detect_user_participation_change(from_number,body,opt_in_keywords,opt_out_keywords)

        if changing_participation_state : 
             update_user_participation(from_number,withdrawal)

        if (body.lower() in [word.lower() for word in opt_in_keywords]) or (body.lower() in [word.lower() for word in opt_out_keywords]):
             return Response(status=204)
            

        response_data = {'response': None, 'sent': False}
        timer = threading.Timer(5.0, send_interim_response, [from_number, response_data])
        timer.start()
        threading.Thread(target=process_openai_response, args=(
            current_app._get_current_object(), from_number, body, response_data, timer, twilio_message_id  # type: ignore
        )).start()
    
        resp = MessagingResponse()
        return Response(str(resp), mimetype="application/xml")


@messages_bp.route("/sms/send", methods=['POST'])
def send_sms():
    phone_number = request.form.get('phone_number')
    message = request.form.get('message')

    if not phone_number or not message:
        flash("Phone number and message are required!", "error")
        return redirect(url_for('sms.send_sms'))

    manager = NewTwilioConversationManager(SMSService())

    try:
        manager.send_message(phone_number, message)
        flash(f"Message sent successfully to {phone_number}!", "success")
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        flash("Failed to send message. Please try again.", "error")

    return redirect(url_for('sms.send_sms'))


@messages_bp.route("/download-messages", methods=["GET"])
@login_required
def download_messages_csv():
    try:
        messages = get_all_messages(filter_assistant_messages=True)

        if len(messages) == 0:
            flash("No messages available for download.", "warning")
            return redirect(url_for("messages.messages_home"))
        
        messages = messages_to_dataframe(messages)
        df = pd.DataFrame(messages)

        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        response = make_response(csv_buffer.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=messages_backup.csv"
        response.headers["Content-Type"] = "text/csv"
        return response

    except Exception as e:
        logger.error(f"Error while exporting messages: {e}")
        flash("An error occurred while trying to download the messages.", "danger")
        return redirect(url_for("messages.messages_home"))
