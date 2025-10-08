# PANDAS QUERY
COLUMNS_OF_INTEREST = ['food_name', 'energy_kcal', 'water', 'protein', 'carbohydrates', 'fat', 'fatty_acids_saturated', 'fiber', 'sodium', 'intake_id']


MEAL_INFO_PROMPT_TEMPLATE = """
    In the case where the user request time related information. This is the current time and date: {current_datetime}.
    Here are some recent meals consumed from the user: {recent_meals}.
    The user is aiming for this dietary goal: {diet_goal}.
    Prepare yourself to be able to give the user nutritional advice based on recenlty consumed meals.

    Any response you formulate MUST NEVER exceed 1100 characters, otherwise the user will never receive it!
    """
REMINDER_PROMPT_TEMPLATE = """
    You are a helpful assistant tasked with generating personalized reminders for users of a food diary app.
    Below is the information about the user and their dietary habits.
    Use this information to create a personalized reminder message.
    This {meal_type} reminder should encourage the user to log their meals, considering their dietary goals, and meal history.

    User Information:
    - Gender: {gender}
    - Age: {age}
    - Dietary Goal: {dietary_goal}
    - Recent Meals: {recent_meals}

    Your reminder should be friendly, motivating, and specific to the user's dietary needs and goals. Consider their recent meals to suggest what they might log next or highlight patterns you see. Provide general observations about their diet and how it aligns with their dietary goals.

    Use the principles of persuasion, primarily Commitment, and occasionally Scarcity, to make the reminders more compelling and less repetitive between one and another.

    Here are some example reminders:

    1. **Commitment**: "Hi there! Don't forget to log your {meal_type}. You've been doing an excellent job staying consistent with your goal of {dietary_goal}. Keeping track of your meals like (some meals that well align with the user's dietary goal) shows your dedication. Keep it up!"

    2. **Commitment**: "Good evening! How was your {meal_type}? Logging your meals helps you stay on track with your {dietary_goal}. Your consistency with meals like (some meals that well align with the user's dietary goal) is impressive. Stay committed!"

    3. **Commitment**: "It's time to log your {meal_type}! Your commitment to {dietary_goal} is evident from your recent meals such as (some meals that well align with the user's dietary goal). Keep logging to maintain your progress!"

    4. **Commitment**: "Hello! Remember to log your meals today. You're making great strides towards {dietary_goal}. Your recent choices, like (some meals that well align with the user's dietary goal), demonstrate your commitment. Fantastic work!"

    5. **Scarcity**: "Hey! Don't miss logging your {meal_type}. Each meal logged is a crucial step towards achieving {dietary_goal}. You’re doing great, and each log is a valuable part of your journey!"

    Use these examples to guide your responses, but feel free to be creative and adjust based on the user's recent meals and specific situation. Generate one personalized reminder message for the user."
    Any response you formulate MUST NEVER exceed 1100 characters, otherwise the user will never receive it!
    Any message you formulate should be analytical, creative, concise and helpful for the user! **NEVER be repetitive!**
"""


WARNING_REMINDER_PROMPT_TEMPLATE = """
You are a helpful assistant tasked with generating personalized reminders for users of a food diary app.  
Below is the information about the user and their dietary habits.  
Use this information to create a friendly and encouraging reminder message.  

The user **has not logged any meals in the past 24 hours**, so your message should gently prompt them to resume tracking.  
Your goal is to **re-engage** the user while being supportive and understanding, rather than making them feel guilty.  
Use **Commitment** as the primary persuasive technique to remind them why they started tracking their meals.  
You may also use **Scarcity** or **Loss Aversion** sparingly to emphasize the value of consistency.  

Additionally, **if they continue not logging for another day, we will stop sending reminders.**  
This should be communicated **gently**—framing it as an option rather than a warning.  

### User Information:  
- Gender: {gender}  
- Age: {age}  
- Dietary Goal: {dietary_goal}  
- Last Logged Meals (if available): {recent_meals}  

### Example Reminders:  

1. **Commitment + Gentle Notice**:  
   "Hey! Haven’t seen a meal log from you in a while. Tracking even one meal can help you stay on course with {dietary_goal}. You’ve done great before with meals like {recent_meals}! Of course, if you’d rather pause for now, we won’t send more reminders after tomorrow—but we’re here when you’re ready!"  

2. **Commitment + Encouragement**:  
   "Hope you’re doing well! Just a friendly nudge to log your meals—consistency is key to {dietary_goal}. You’ve made great choices before, like {recent_meals}. If now isn’t the right time, that’s okay! We’ll check in once more tomorrow, but you’re always welcome back when ready!"  

3. **Scarcity/Loss Aversion + Gentle Notice**:  
   "Hey there! Every meal log keeps you on track toward {dietary_goal}. We know life gets busy, but even a small step today helps! If you’re taking a break, we won’t keep nudging after tomorrow—but we’d love to see you back anytime!"  

4. **Commitment + Soft Reminder**:  
   "Tracking helps you see your progress, and you’ve done so well before! Just a little reminder to log your meals today. If now isn’t the best time, no worries—we’ll send one last check-in tomorrow, and after that, we’ll step back until you're ready!"  

Use these examples as a guide, but adapt each reminder to be specific to the user's dietary goals and past tracking behavior.  
Keep it **concise, engaging, and under 1100 characters.** **Never be repetitive!**  

"""


# OPENAI
GPT_4_O = "gpt-4o"
GPT_4_1_MINI = "gpt-4.1-mini"
GPT_4_1 = "gpt-4.1"
GPT_4_0_MINI = "gpt-4o-mini"
GPT_4_TURBO = "gpt-4-turbo"
GPT_3_TURBO = "gpt-3-turbo"
ASSISTANT_ROLE = "assistant"
SYSTEM_ROLE = "system"
USER_ROLE = "user"

# FILESYSTEM
COHORT_ANNOTATIONS_CSV_FILENAME = "cohort_annotation_items.csv"
UPDATE_GOOGLE_FORM_CSV_FILENAME = "updating_google_form_users_data.csv"
GOOGLE_FORM_CSV_FILENAME = "google_form_users_data.csv"
DATA_FOLDER_NAME = "data"
DATABASE_FILENAME = "mydatabase.db"
FOODS_CATEGORIES_FILENAME = "category_list.csv"
FOODS_EXPORT_FILENAME = "foods-export-2025-04-10.csv"
PRODUCTS_CATEGORIES_FILENAME = "products_category_list.csv"
PRODUCTS_FILENAME = "products.csv"
OUTPUT_FOLDER = "output"
FIGURE_OUTPUT_FOLDER = "figures"
TEXT_OUTPUT_FOLDER = "text_summaries"


# MYFOODREPO ENVIRONMENT KEY NAMES
MFR_ENV_KEY = "MFR_DATA_ENV"
MFR_COHORT_ID_KEY = "MFR_COHORT_ID"


# MYFOODREPO APP LINKS
ANDROID_APP_LINK = "https://play.google.com/store/apps/details?id=ch.digitalepidemiologylab.myfoodrepo2"
IOS_APP_LINK = "https://apps.apple.com/ch/app/myfoodrepo/id1450244793"

#FEEDBACK SURVEY LINK
FEEDBACK_SURVEY =  "https://docs.google.com/forms/d/e/1FAIpQLSfFC5RKuE15l8GZ0PEDm2_JCaxPh7JwTb3_lMiRACiGaIGdPw/viewform?usp=dialog"

# TWILIO
WHATSAPP_SENDER_ID = "MGa908fd80159c3705b703a3c8bfd61d96"
SMS_SENDER_ID = "MGf890ba97706924a58df9ccb5329528bf"


# OTHER
DB_UPDATE_TIME_INTERVAL = 1
DB_UPDATE_DAYS_WINDOW = 3
USERS_MESSAGES_LIMIT = 10
