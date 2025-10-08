from langchain_openai import ChatOpenAI
import openai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain_community.chat_message_histories import ChatMessageHistory

from src.communication.chat_history import DBChatMessageHistory

from src.prompts.prompts_templates import DEFAULT_SYSTEM_PROMPT

from src.config.logging_config import Logger
from src.constants import SYSTEM_ROLE,GPT_4_O, GPT_4_1_MINI
from src.data_manager.message import (db_add_message,
                                      db_add_message_from_phone_number,
                                      get_user_messages)
from src.data_manager.user import get_user

logger = Logger('openai_client').get_logger()

@retry(
    wait=wait_random_exponential(min=1, max=300), 
    stop=stop_after_attempt(10))
def safe_invoke_chain(chain, input_data, config):
    try:
        return chain.invoke(input_data, config=config)
    except Exception as e:
        logger.error(f"Error in safe_invoke_chain: {e}")
        

class OpenAIChatClient:
    """
    A class representing a chat client that interacts with OpenAI for generating responses.

    Attributes:
        api_key (str): The API key for accessing OpenAI services.

    Methods: #TODO : Put methods here.

    """


    def __init__(self, api_key):
        """
        Initializes the OpenAIChatClient object.

        Args:
            api_key (str): The API key for accessing OpenAI services.
        """
        self.api_key = api_key
        openai.api_key = self.api_key

        self.llm = ChatOpenAI(temperature=1,model=GPT_4_O, api_key=self.api_key)

        self.prompt = ChatPromptTemplate.from_messages([
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])

        self.chain_with_history = RunnableWithMessageHistory(
            self.prompt | self.llm,
            get_session_history=self.get_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )

    def get_history(self,session_id):
        logger.debug(f"Fetching history for session_id: {session_id}")
        history = DBChatMessageHistory(session_id)
        #logger.debug(f"Retrieved history: {history}")
        return history

    def initialize_conversation(self, phone_number):
        """
        Sets up the initial instructions for the AI on how to behave in conversations.

        Args:
            phone_number (str): The phone number of the user.

        Returns:
            None
        """
        user = get_user(phone_number)
        if user:
            self.add_message(user.id, SYSTEM_ROLE, DEFAULT_SYSTEM_PROMPT,twilio_message_id = None, reminder_id=None)

    def add_message(self, user_id, role, content,twilio_message_id,reminder_id):
        """
        Adds a message to the conversation history in the database.

        Args:
            user_id (int): The ID of the user.
            role (str): The role of the message (e.g., "user", "assistant").
            content (str): The content of the message.

        Returns:
            None
        """
        
        db_add_message(user_id, role, content, twilio_message_id,reminder_id)

    def add_message_from_phone_number(self, phone_number, role, content,twilio_message_id,reminder_id):
        """
        Adds a message to the conversation history in the database.

        Args:
            user_id (int): The ID of the user.
            role (str): The role of the message (e.g., "user", "assistant").
            content (str): The content of the message.

        Returns:
            None
        """
    
        status_log, status = db_add_message_from_phone_number(phone_number, role, content, twilio_message_id,reminder_id)
        if status != 200:
            logger.error(status_log)

    def get_user_messages(self, user_id):
        """
        Retrieves all messages for a specific user from the database.

        Args:
            user_id (int): The ID of the user.

        Returns:
            list: A list of dictionaries containing the role and content of each message.
        """
        messages = get_user_messages(user_id)
        return [{"role": message.role, "content": message.content, "timestamp": message.datetime} for message in messages]
    

    def create_chat_completion(self, model, phone_number, temperature):
        try:
            user = get_user(phone_number)
            if not user:
                logger.error("User NOT FOUND")
                return "User not found."

            messages = self.get_user_messages(user.id)
            if not messages:
                self.initialize_conversation(phone_number)
                messages = self.get_user_messages(user.id)

            last_input = messages[-1]["content"]

            message_history = DBChatMessageHistory(phone_number)

            logger.debug("Trying to formulate a response...")
            response = safe_invoke_chain(
                        self.chain_with_history,
                        {"input": last_input},
                        {
                            "configurable": {
                                "session_id": phone_number,
                                "message_history": message_history,
                            }
                        }
                    )

            #logger.debug(f"Model response: {response.content}")
            return response.content

        except openai.RateLimitError as e:
            logger.warning(f"Rate limit exceeded: {e}")
            return "RateLimitError"

        except openai.OpenAIError as e:
                logger.error(f"OpenAI API error: {e}")
                return "OpenAIError"

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            return "UnexpectedError"

