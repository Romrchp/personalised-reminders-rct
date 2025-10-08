# MyFoodRepo LLM Test - AI-enhanced reminders & Conversational agent

This project integrates a large language model (LLM) to enhance user engagement in the MyFoodRepo app through personalized interactions, reminders, and chatbot functionalities. The system is tested across four distinct study groups with varying levels of interaction and reminders.

## Table of Contents
- [Project Description](#project-description)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Endpoints](#endpoints)
- [Architecture](#architecture)

## Project Description
The aim of this project was to enhance the user experience of the MyFoodRepo app by leveraging an LLM to provide personalized interactions. This included sending reminders to log food, giving personalized nutrition advice, and more.

## Features
- Welcome message for all users.
- No reminders and no chatbot (**Group 0**)
- Basic reminders to log food (**Group 1**).
- Chatbot for personalized nutrition advice (**Group 2** and **3**).
- Personalized reminders and chatbot (**Group 3**).

![Table](/assets/study_groups_table.png)

## Installation

### Prerequisites
- Python 3.x
- pip (Python package installer)

### Clone the Repository
```bash
git clone https://github.com/digitalepidemiologylab/myfoodrepo-llm-test.git
cd myfoodrepo-llm-test
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Virtual Environment
*(Optional)* Create a virtual environment using *Conda* or *venv*. 

### Environment Variables
Set up the necessary environment variables.  
Create a .env file in the root directory with the following content:

```dotenv
MFR_DATA_ENV=MyFoodRepo environment ('local', 'production')
MFR_COHORT_ID=MyFoodRepo cohort ID
MFR_ACCESS_TOKEN=your MyFoodRepo token
MFR_UID=your MyFoodRepo email
MFR_CLIENT=MyFoodRepo client id

OPENAI_API_KEY=your openai api key

TWILIO_ACCOUNT_SID=your Twilio account ID
TWILIO_AUTH_TOKEN=your Twilio auth token
TWILIO_PHONE_NUMBER=your Twilio phone number
TWILIO_SMS_SENDER_ID=your Twilio sender ID

NGROK_TUNNEL= ngrok address

CERT_PATH=your certificate path for SSL connections
KEY_PATH=your key path for SSL connections
```

## Usage
To start the flask service simply run your preferred Python version (if you are using a virtual environment, use that one).
```bash
python web_app.py
```

Once the flask service is running, ensure that the [**Twilio's Webhook**](https://www.twilio.com/docs/usage/webhooks) is pointing at your address.  
This will allow the service to process the reply messages received from the users.

You can either:
- Provide a tunnel (using [ngrok](https://ngrok.com/), on your local machine for testing purposes)
- Provide the domain of your purchased service, if any


> Note: Only users in groups 2 and 3 are allowed to chat. Ensure they are registered in the system through the API or the database.


### Configuration
To configure and start the project correctly:  
1. Collect data from the Google Form data.
2. Insert User data into the DB with the `init` endpoint.
3. Add reminders for all users with the `add_all_reminders` endpoint.
4. Schedule all reminders (automatic on server run).
5. Send Welcome Message with the `start` endpoint.  

> Note: The flask app will automatically create at the first run the *SQLite Database* and the *myfoodrepo.log* file.

### Endpoints
- `sms_reply`: Handle incoming messages
- `add_all_reminders`: Add reminders on the db for all users of Group 1 and 3
- `init`: Populates DB from .csv file originated from the Google Form data
- `start`: Send welcome message to all participants

## Architecture

## Main Repository Structure & Most important files

 📂 [results_analysis](results_analysis/) :  Contains a notebook with the results of the RCT conducted during the project.


- 📂 [src](src/) : Main folder containing the entire back-end Python code of the framework used in the RCT.
    -  📂 [communication](src/communication/) : Contains all files related to communication with the users (Message history, Sending reminders, messages, mails...)
    -  📂 [config](src/config/) : Various configuration files
    -  📂 [data_manager](src/data_manager/) : Basis / Main data managing files : Meals, users, Reminders, Messages...
    -  📂 [locales](src/locales/) : FR, EN, IT, and DE files containing all necessary static information.
    -  📂 [prompt_engineering](src/prompt_engineering/): All files related to Reminders building process & evaluation.
    -  📂 [prompts](src/prompts/) : Contains all prompt components used in throughout the project.
    -  📂 [response_manager](src/response_manager/) : Handles the responses to users messages, with openAI as well.
    -  📂 [routes](src/routes/) : Contains all routes for the Front-End part of the Flask App.¨
    -  📂 [scheduler](src/scheduler/): Handles correctly all scheduler related operations.
    -  📂 [services](src/services/): Some services used throughout the project.
    -  📂 [utils](src/utils/): Utils used throughout the project.

- 📂 [static](static/): All static CSS, JS & images elements needed for the front-end admin dashboard.
- 📂 [templates](templates/): All HTML templates used in the admin dashboard.


- 📄 [web_app.py](web_app.py): Main file to run in order to create and use the Flask application created in this project.



### Overall Architecture
The MyFoodRepo LLM Test project follows a modular monolithic architecture. The system is designed to enhance user engagement through personalized interactions, reminders, and chatbot functionalities, divided into specific modules for clarity and maintainability.

### Components
The main components of the project are:

- **Communication Module**: Implements Twilio integration functionalities, including an abstraction of a Messaging Service to use both SMS and WhatsApp.
- **Config Module**: Manages the creation of the database, the Flask app, the scheduler, and the logging mechanism.
- **Data Manager Module**: Defines the schema, handles database interactions and MyFoodRepo API interactions, and processes data such as Google form data to initialize the database with user data.
- **Locales Directory**: Provides localized strings for the three supported languages (English, French, German).
- **OpenAI Client Module**: Handles interactions with OpenAI, including chat completions.
- **Response Module**: Manages the generation of responses.
- **Scheduler Module**: Handles the scheduling of data fetching from the MyFoodRepo API and sending automated reminders.
- **Services Module**: Provides basic data processing for meal filtering and grouping.
- **Utils Module**: Contains helper functions for other modules.

### Data Flow
1. **User Inputs**: Users interact with the system through SMS.
2. **Processing**: Messages are processed by the Flask web app, which routes them to the appropriate modules.
3. **Storage**: Data is stored in a SQLite database.
4. **Outputs**: Responses are sent back to users via SMS, and reminders are scheduled as needed.

### Technologies
The project uses the following technologies and frameworks:
- **Flask**: Web framework for building the API and handling HTTP requests.
- **SQLAlchemy**: ORM for database interactions.
- **Twilio**: Service for sending and receiving SMS messages.
- **OpenAI**: Service for generating chatbot responses.
- **APScheduler**: For scheduling tasks.
- **Pandas**: For data manipulation and analysis.

### Database
The project uses SQLite for data storage. The database schema includes the following tables:
- **User**: Stores user information.
- **Meals**: Logs of meals consumed by users.
- **Messages**: Logs of messages sent and received by users.
- **Reminders**: Stores reminders set for users.

### APIs
The project interacts with the following APIs:
- **Twilio API**: For sending and receiving SMS messages.
- **OpenAI API**: For generating chatbot responses.
- **MyFoodRepo API**: For fetching user data and meal logs.

### Communication
The system communicates with external services like Twilio for sending and receiving SMS messages, and OpenAI for generating chatbot responses. Secure API keys and tokens are used to authenticate these communications.

### Scheduler
Two main jobs are scheduled:
1. **Sending Reminders**: Reminders are sent to users at specified times based on their study group configurations.
2. **Database Sync**: The system synchronizes data with the MyFoodRepo API to keep the database updated with the food consumed by users.

### Security
Environment variables are used to manage sensitive information such as API keys and tokens. The system ensures secure communication with external services using HTTPS.

### Error Handling
Errors and exceptions are logged using a custom logging configuration. The system provides detailed error messages and ensures that any critical issues are reported and handled gracefully.


