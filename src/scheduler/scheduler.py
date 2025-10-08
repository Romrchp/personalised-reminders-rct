import atexit
import os
import pytz
import time
import sys
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime, timedelta

from ..communication.reminder_manager import send_reminder
from ..config.logging_config import Logger
from ..constants import DB_UPDATE_TIME_INTERVAL
from ..data_manager.models import User, db
from ..data_manager.myfoodrepo_data_manager import update_database

logger = Logger('myfoodrepo.scheduler').get_logger()

executors = {
    'default': ThreadPoolExecutor(50),  
}
job_defaults = {
    'coalesce': False, 
    'max_instances': 1, 
    'misfire_grace_time': 300 
}

scheduler = BackgroundScheduler(executors=executors, job_defaults=job_defaults)

scheduler = BackgroundScheduler()
timezone = pytz.timezone('Europe/Zurich')
job_execution_log = {}

class FlaskAppProxy:
    def __init__(self, app_import_path):
        self.app_import_path = app_import_path
        
    def get_app(self):
        """
        Dynamically imports and creates a Flask app on demand
        This ensures we always have a valid app context
        """
        try:
            
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
                
            
            if '.' in self.app_import_path:
                module_path, app_name = self.app_import_path.rsplit('.', 1)
                module = __import__(module_path, fromlist=[app_name])
                app = getattr(module, app_name)
            else:
                
                module = __import__(self.app_import_path)
                app = getattr(module, 'app') 
                
            return app
        except Exception as e:
            logger.error(f"Error importing app: {str(e)}")
            return None


app_proxy = FlaskAppProxy('web_app') 


def log_job_execution(job_id, status, error_msg=None):
    """Track job execution status"""
    timestamp = datetime.now(timezone)
    job_execution_log[job_id] = {
        'timestamp': timestamp,
        'status': status, 
        'error': error_msg
    }
    logger.info(f"Job {job_id} - Status: {status} at {timestamp}")


def fetch_meal_data():
    """Function to update database with latest meal data"""
    try:
        app = app_proxy.get_app()
        if app:
            with app.app_context():
                update_database()
                logger.info("Successfully updated database")
        else:
            logger.error("Could not get app reference for fetch_meal_data")
    except Exception as e:
        logger.error(f"Error in fetch_meal_data: {str(e)}")

def fetch_meal_data_recent():
    """Function to update database with only partial sync (full_sync=False)"""
    try:
        app = app_proxy.get_app()
        if app:
            with app.app_context():
                update_database(full_sync=False)
                logger.info("Successfully updated database with full_sync=False")
        else:
            logger.error("Could not get app reference for fetch_meal_data_recent")
    except Exception as e:
        logger.error(f"Error in fetch_meal_data_recent: {str(e)}")


def schedule_recent_sync_jobs():
    """Schedule three jobs for partial database sync at 6:59, 11:59, and 18:59"""
    scheduler.add_job(
        fetch_meal_data_recent,
        trigger='cron',
        hour=6,
        minute=57,
        id='partial_sync_0659',
        timezone=timezone,
        replace_existing=True
    )
    scheduler.add_job(
        fetch_meal_data_recent,
        trigger='cron',
        hour=11,
        minute=57,
        id='partial_sync_1159',
        timezone=timezone,
        replace_existing=True
    )
    scheduler.add_job(
        fetch_meal_data_recent,
        trigger='cron',
        hour=18,
        minute=57,
        id='partial_sync_1859',
        timezone=timezone,
        replace_existing=True
    )



def schedule_fetch_meal_data():
    """Schedule periodic database updates"""
    scheduler.add_job(
        fetch_meal_data,
        'interval',
        hours=DB_UPDATE_TIME_INTERVAL,
        id='fetch_meal_data',
        replace_existing=True
    )


def execute_reminder(user_id, meal_type, reminder_id):
    """
    Execute a reminder job. This function will be called by the scheduler.
    """
    job_id = f'reminder_{reminder_id}'
    log_job_execution(job_id, 'started')

    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):

        try:
            app = app_proxy.get_app()
            if not app:
                logger.error("Could not get app reference for execute_reminder")
                return

            with app.app_context():
                user = User.query.get(user_id)
                if user:
                    send_reminder(user, meal_type, app, reminder_id)
                    logger.info(f"Reminder {reminder_id} sent to user {user_id}")
                    log_job_execution(job_id, 'completed')
                    return
                else:
                    raise Exception(f"Problem with the reminder job")
        except Exception as e:
            
            error_msg = f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}"
            logger.error(f"Error in execute_reminder for user {user_id}, reminder {reminder_id}: {error_msg}")
            
            if attempt < max_retries - 1: 
                logger.info(f"Retrying reminder {reminder_id} in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else: 
                log_job_execution(job_id, 'failed', str(e))


def schedule_reminders(app):
    """Schedule all reminders for users in study groups 1 and 3"""
    logger.info("Scheduling reminders for all users...")
    
    with app.app_context():
        try:
            all_users = User.query.filter(User.study_group.in_([1, 3])).all()
            thread_pool_size = 20
            stagger_interval = 10
            job_count = 0
            
            for user in all_users:
                for reminder in user.reminders:
                    logger.debug(f"Scheduling Reminder:{reminder.id} for User:{user.id}")
                    batch_number = job_count // thread_pool_size
                    stagger_seconds = batch_number * stagger_interval

                    #we handle minute overflowing 
                    stagger_minute_offset = stagger_seconds // 60
                    stagger_seconds = stagger_seconds % 60
                    
                    # job schedulinggggg
                    scheduler.add_job(
                        func=execute_reminder,
                        args=[user.id, reminder.meal_type, reminder.id],
                        trigger='cron',
                        hour=reminder.time.hour,
                        minute=reminder.time.minute + stagger_minute_offset,
                        second=stagger_seconds,
                        replace_existing=True,
                        timezone=timezone,
                        id=f'reminder_{reminder.id}'
                    )
                    job_count +=1
        except Exception as e:
            logger.error(f"Error scheduling reminders: {str(e)}")


def unschedule_job(job_id):
    """Remove a scheduled job"""
    try:
        scheduler.remove_job(job_id)
        logger.info(f"Job {job_id} removed successfully")
        return "Job removed", 200
    except Exception as e:
        logger.error(f"Failed to remove job {job_id}: {str(e)}")
        return f"Failed to remove the job: {str(e)}", 400


def get_reminder_stagger_offset(reminder_time, reminder_id):
    """Calculate stagger offset for a reminder based on existing reminders at the same time"""
    try:

        all_users = User.query.filter(User.study_group.in_([1, 3])).all()
        
        same_time_reminders = []
        for user in all_users:
            for r in user.reminders:
                if (r.time.hour == reminder_time.hour and 
                    r.time.minute == reminder_time.minute):
                    same_time_reminders.append(r.id)
        
        # find where the current reminder stands
        same_time_reminders.sort()
        if reminder_id in same_time_reminders:
            job_position = same_time_reminders.index(reminder_id)
        else:
            job_position = len(same_time_reminders)  
        
        # we compute the staggering
        thread_pool_size = 20
        stagger_interval = 5
        batch_number = job_position // thread_pool_size
        stagger_seconds = batch_number * stagger_interval
        
        # minute overflow if needed
        stagger_minute_offset = stagger_seconds // 60
        stagger_seconds = stagger_seconds % 60
        
        return stagger_minute_offset, stagger_seconds
        
    except Exception as e:
        logger.error(f"Error calculating stagger offset: {str(e)}")
        return 0, 0 


def schedule_reminder(user_id, reminder_id, _meal_type, app):
    """Schedule or reschedule a specific reminder with dynamic staggering"""
    try:
        with app.app_context():
            user = User.query.get(user_id)
            reminder = next((r for r in user.reminders if r.id == reminder_id), None)

            if user and reminder:
                logger.debug(f"Scheduling Reminder:{reminder.id} for User:{user.id}")


                stagger_minute_offset, stagger_seconds = get_reminder_stagger_offset(
                    reminder.time, reminder.id
                )

                scheduler.add_job(
                    func=execute_reminder,
                    args=[user.id, reminder.meal_type, reminder.id],
                    trigger='cron',
                    hour=reminder.time.hour,
                    minute=reminder.time.minute + stagger_minute_offset,
                    second=stagger_seconds,
                    replace_existing=True,
                    timezone=timezone,
                    id=f'reminder_{reminder.id}'
                )
                return 200
            else:
                logger.error(f"Failed to schedule reminder: User {user_id} or reminder {reminder_id} not found")
                return 400
    except Exception as e:
        logger.error(f"Error in schedule_reminder for user {user_id}, reminder {reminder_id}: {str(e)}")
        return 400


def start_scheduler(app):
    """Initialize and start the scheduler"""
    try:
        with app.app_context():
            schedule_reminders(app)
            schedule_fetch_meal_data()
            schedule_recent_sync_jobs()
            
        jobs_scheduled = scheduler.get_jobs()
        for job in jobs_scheduled:
            if hasattr(job.trigger, 'fields'):
                hour_field = job.trigger.fields[2]
                logger.info(f"Job ID: {job.id}, Hour: {hour_field}")
            else:
                logger.info(f"Job ID: {job.id}, Trigger: {job.trigger}")
                
        scheduler.start()
        logger.info("Scheduler started successfully")
        atexit.register(stop_scheduler)
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")


def get_all_running_jobs():
    """Get all currently scheduled jobs"""
    return scheduler.get_jobs()

def get_job_execution_report():
    """Get a report of job execution status"""
    report = {
        'total_jobs': len(job_execution_log),
        'completed': 0,
        'failed': 0,
        'started_but_not_completed': 0,
        'details': []
    }
    
    for job_id, log_entry in job_execution_log.items():
        if log_entry['status'] == 'completed':
            report['completed'] += 1
        elif log_entry['status'] == 'failed':
            report['failed'] += 1
        elif log_entry['status'] == 'started':
            report['started_but_not_completed'] += 1
            
        report['details'].append({
            'job_id': job_id,
            'timestamp': log_entry['timestamp'],
            'status': log_entry['status'],
            'error': log_entry.get('error')
        })
    
    logger.info(f"Job execution report: {report['completed']} completed, {report['failed']} failed, {report['started_but_not_completed']} incomplete")
    return report

def clear_old_job_logs(hours_old=24):
    """Clear job execution logs older than specified hours"""
    cutoff_time = datetime.now(timezone) - timedelta(hours=hours_old)
    jobs_to_remove = []
    
    for job_id, log_entry in job_execution_log.items():
        if log_entry['timestamp'] < cutoff_time:
            jobs_to_remove.append(job_id)
    
    for job_id in jobs_to_remove:
        del job_execution_log[job_id]
    
    logger.info(f"Cleared {len(jobs_to_remove)} old job logs")


def stop_scheduler():
    """Stop the scheduler"""
    try:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")


def pause_scheduler():
    """Pause the scheduler"""
    try:
        scheduler.pause()
        logger.info("Scheduler paused")
    except Exception as e:
        logger.error(f"Error pausing scheduler: {str(e)}")


def resume_scheduler():
    """Resume the scheduler"""
    try:
        scheduler.resume()
        logger.info("Scheduler resumed")
    except Exception as e:
        logger.error(f"Error resuming scheduler: {str(e)}")
