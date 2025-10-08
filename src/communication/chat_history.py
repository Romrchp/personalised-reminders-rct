from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableWithMessageHistory
from src.data_manager.user import get_user
from src.data_manager.message import get_user_messages
from src.config.logging_config import Logger

logger = Logger('chat_history').get_logger()

class DBChatMessageHistory(BaseChatMessageHistory):
    """
    Structure class for the chat history to provide the LLM with
    
    """
    def __init__(self, phone_number):
        self.user = get_user(phone_number)
        logger.debug(f"✅ Found user {self.user.id} with phone number {phone_number}")
        if not self.user:
            logger.warning(f"🛑 No user found for phone number: {phone_number}")

    @property
    def messages(self):
        if not self.user:
            return []

        db_messages = get_user_messages(self.user.id)
        chat_messages = []

        most_recent_system = None
        for msg in reversed(db_messages):
            if msg.role == "system":
                most_recent_system = msg.content
                break
        
        if most_recent_system:
            chat_messages.append(SystemMessage(content=most_recent_system))

        for msg in db_messages:
            role = msg.role
            content = msg.content

            if role == "user":
                chat_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                chat_messages.append(AIMessage(content=content))
        return chat_messages

    def add_message(self, message):
        pass

    def clear(self):
        pass


