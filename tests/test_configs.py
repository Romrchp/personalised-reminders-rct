import unittest
from unittest.mock import patch, mock_open, MagicMock
from parameterized import parameterized
import logging
import sys
from flask import Flask
from ..src.config.config import load_localizations, setup_scheduler, configure_db, create_app
from ..src.config.logging_config import Logger  


class TestAppFunctions(unittest.TestCase):

    @parameterized.expand([
        (["en.json"], {"en": {"key": "value"}}),
        (["fr.json", "de.json"], {"fr": {"key": "value"}, "de": {"key": "value"}}),
        ([], {}),
    ])
    @patch("your_module.os.listdir")
    @patch("your_module.open", new_callable=mock_open, read_data='{"key": "value"}')
    @patch("your_module.json.load", return_value={"key": "value"})
    def test_load_localizations(self, mock_filenames, expected_output, mock_json_load, mock_open, mock_listdir):
        mock_listdir.return_value = mock_filenames
        result = load_localizations()
        self.assertEqual(result, expected_output)
        mock_listdir.assert_called_once()
        mock_open.assert_called()
        mock_json_load.assert_called()

    @patch("your_module.start_scheduler")
    def test_setup_scheduler(self, mock_start_scheduler):
        app = Flask(__name__)
        setup_scheduler(app)
        mock_start_scheduler.assert_called_once_with(app)

    @patch("your_module.os.makedirs")
    @patch("your_module.os.path.exists", return_value=False)
    @patch("your_module.db.init_app")
    @patch("your_module.db.create_all")
    @patch("your_module.init_db")
    def test_configure_db(self, mock_init_db, mock_create_all, mock_init_app, mock_exists, mock_makedirs):
        app = Flask(__name__)
        configure_db(app)

        mock_exists.assert_called_once()
        mock_makedirs.assert_called_once()
        mock_init_app.assert_called_once_with(app)
        mock_create_all.assert_called()
        mock_init_db.assert_called()

    @patch("your_module.load_dotenv")
    @patch("your_module.configure_db")
    @patch("your_module.setup_scheduler")
    @patch("your_module.load_localizations", return_value={"en": {"key": "value"}})
    def test_create_app(self, mock_load_localizations, mock_setup_scheduler, mock_configure_db, mock_load_dotenv):
        app = create_app()
        self.assertIsInstance(app, Flask)
        self.assertIn("localizations", app.extensions)
        self.assertEqual(app.extensions["localizations"], {"en": {"key": "value"}})
        mock_load_dotenv.assert_called_once()
        mock_configure_db.assert_called_once_with(app)
        mock_setup_scheduler.assert_called_once_with(app)


class TestLogger(unittest.TestCase):

    @patch("your_module.logging.getLogger")
    def test_logger_initialization(self, mock_get_logger):
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance

        logger = Logger("TestLogger")
        self.assertEqual(logger.logger, mock_logger_instance)
        mock_get_logger.assert_called_once_with("TestLogger")

    @patch("your_module.logging.FileHandler")
    @patch("your_module.logging.StreamHandler")
    def test_logger_handlers(self, mock_stream_handler, mock_file_handler):
        logger = Logger("TestLogger")

        # Ensure two handlers are added
        handlers = logger.logger.handlers
        self.assertEqual(len(handlers), 2)

        # Check if handler levels are correct
        stream_handler = [h for h in handlers if isinstance(h, logging.StreamHandler)][0]
        file_handler = [h for h in handlers if isinstance(h, logging.FileHandler)][0]

        self.assertEqual(stream_handler.level, logging.INFO)
        self.assertEqual(file_handler.level, logging.DEBUG)

    @patch("your_module.logging.FileHandler")
    @patch("your_module.logging.StreamHandler")
    def test_logger_logs_messages(self, mock_stream_handler, mock_file_handler):
        logger = Logger("TestLogger").get_logger()

        with patch.object(logger, "info") as mock_info, patch.object(logger, "debug") as mock_debug:
            logger.info("This is an info message")
            logger.debug("This is a debug message")

            mock_info.assert_called_once_with("This is an info message")
            mock_debug.assert_called_once_with("This is a debug message")


if __name__ == "__main__":
    unittest.main()

