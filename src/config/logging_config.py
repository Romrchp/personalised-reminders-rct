import logging
import sys


class Logger:
    """
    A configurable logging utility for managing application logs.

    This class initializes a logger with both console and file handlers, ensuring that:
    - Console logs capture messages at the INFO level or higher.
    - File logs capture messages at the DEBUG level or higher.
    - Logs are formatted with timestamps, logger names, log levels, and messages.

    Attributes:
        logger (logging.Logger): The configured logger instance.
    """

    def __init__(self, name, level=logging.DEBUG):

        """
        Initializes the logger with a specified name and logging level.

        Args:
            name (str): The name of the logger.
            level (int, optional): The logging level.

        The logger includes:
        - A stream handler (console output) with INFO level logging.
        - A file handler (`myfoodrepo.log`) with DEBUG level logging.
        - A standardized log format for both handlers.

        Ensures that multiple handlers are not added if the logger already has them.
        """

        self.logger = logging.getLogger(name)
        if not self.logger.hasHandlers():
            self.logger.setLevel(level)

            # Create the handlers
            c_handler = logging.StreamHandler(sys.stdout)
            c_handler.setLevel(logging.INFO)

            f_handler = logging.FileHandler('myfoodrepo.log',encoding='utf-8')
            f_handler.setLevel(logging.DEBUG)

            # Create the formatters and then add it to handlers
            logging_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            c_format = logging.Formatter(logging_format)
            f_format = logging.Formatter(logging_format)

            c_handler.setFormatter(c_format)
            f_handler.setFormatter(f_format)

            # Add handlers to the logger
            self.logger.addHandler(c_handler)
            self.logger.addHandler(f_handler)

    def get_logger(self): 
        return self.logger
