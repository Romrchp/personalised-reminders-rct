# Master Thesis - AI-Enhanced Reminders for Food Tracking Adherence: A Randomised Controlled Trial

This repository contains all components used to conduct a randomized controlled trial (RCT) investigating the impact of personalized reminders on users' food tracking adherence within the MyFoodRepo (MFR) application. Implementation details and results are available in the project report but installation guidelines will not be detailed here.


## Table of Contents
- [Project Description](#project-description)
- [Detailed Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Endpoints](#endpoints)
- [Architecture](#architecture)

## Project Description

The aim of the project was to study the impact of personalised interactions on user experience, through the [MyFoodRepo](https://www.myfoodrepo.ai/en) application developed within the Digital Epidemiology Lab, at EPFL. As app development was not considered for this specific project, we decided to develop an fully functional and automized Flask-based web application that would handle all features (see below) for the duration of the RCT. 
Throughout the project, we aim to study personalisation under two main axes : personalised reminders & chatbot interactions, which were the main features developed and handled by the aforementioned architecture. Moreover, to be able to fully assess the impact of personalisation, we also implemented static reminders in order to separate the "reminder" effect from the "personalisation" effect, if any.


## Features

All users have been randomly spread in 4 distinct groups, detailed just below.

![Table](/assets/study_groups_table.png)

The features can therefore be listed as follows :

- A "Welcome message" was sent to all users, independently of the randomisation.
- **Group 0** : No reminders nor chatbot interaction.
- **Group 1** : Static reminders to log their food activity on the app, no chatbot interaction.
- **Group 2** : No reminders, but chatbot availability for personalised nutritional advice.
- **Group 3** : Personalised reminders and chatbot availability.

All code related work to develop these features can be found in the files of the project, mostly under 📂[src](src/)


## Architecture

## Main Repository Structure & Most important files

The MyFoodRepo LLM Test project follows a modular monolithic architecture. The system is designed to enhance user engagement through personalized interactions, reminders, and chatbot functionalities, divided into specific modules for clarity and maintainability.

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

- 📄 [Master Thesis Report](Master_Thesis): Final report of the master thesis.



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

### Security
Environment variables are used to manage sensitive information such as API keys and tokens. The system ensures secure communication with external services using HTTPS.

### Error Handling
Errors and exceptions are logged using a custom logging configuration. The system provides detailed error messages and ensures that any critical issues are reported and handled gracefully.


