"""Unit tests do not require PostgreSQL or psycopg to be installed."""

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from src import app
from src.app import ConfigurationError, connection_parameters, load_settings


VALID_CONFIG = (
    '[database]\nhost="127.0.0.1"\nport=5432\ndbname="seminar_db"\n'
    'connect_timeout=5\nsslmode="disable"\n'
)


class ConfigurationTests(unittest.TestCase):
    def assert_invalid_config(self, content):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            path.write_text(content, encoding="utf-8")
            with self.assertRaises(ConfigurationError):
                load_settings(path)

    def test_rejects_non_string_and_unknown_ssl_modes(self):
        # Arrays and inline tables used to leak an unhandled TypeError.
        for value in ('[]', '{}', 'true', '5', '"prefer"'):
            with self.subTest(sslmode=value):
                self.assert_invalid_config(VALID_CONFIG.replace('"disable"', value))

    def test_rejects_invalid_parameter_types_and_ranges(self):
        for old, new in (
            ('host="127.0.0.1"', 'host=" "'),
            ('dbname="seminar_db"', 'dbname=[]'),
            ('port=5432', 'port=true'),
            ('port=5432', 'port=0'),
            ('port=5432', 'port=65536'),
            ('connect_timeout=5', 'connect_timeout="5"'),
            ('connect_timeout=5', 'connect_timeout=0'),
            ('connect_timeout=5', 'connect_timeout=61'),
        ):
            with self.subTest(setting=new):
                self.assert_invalid_config(VALID_CONFIG.replace(old, new))

    def test_rejects_missing_or_unexpected_sections_and_keys(self):
        for content in (
            '',
            'database="invalid"\n',
            VALID_CONFIG.replace('port=5432\n', ''),
            VALID_CONFIG + '\n[other]\nvalue=1\n',
            VALID_CONFIG + 'password="must_not_be_in_config"\n',
            '[database\n',
        ):
            with self.subTest(content=content):
                self.assert_invalid_config(content)

    def test_missing_file_reports_configuration_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ConfigurationError):
                load_settings(Path(directory) / "missing.toml")


class ConnectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings = load_settings()

    def test_settings_are_loaded(self):
        self.assertEqual(self.settings["host"], "127.0.0.1")
        self.assertEqual(self.settings["dbname"], "seminar_db")

    def test_extra_options_in_username_are_data(self):
        injected_username = "seminar_user host=malicious.example port=9999 sslmode=disable"
        params = connection_parameters(self.settings, injected_username, "not_a_real_password")
        self.assertEqual(params["user"], injected_username)
        self.assertEqual(params["host"], "127.0.0.1")
        self.assertEqual(params["port"], 5432)
        self.assertEqual(params["dbname"], "seminar_db")
        self.assertEqual(set(params), {"host", "port", "dbname", "connect_timeout", "sslmode", "user", "password"})

    def test_extra_options_in_password_are_data(self):
        malicious_password = "x' host=malicious.example user=postgres options=-cstatement_timeout=0"
        params = connection_parameters(self.settings, "seminar_user", malicious_password)
        self.assertEqual(params["password"], malicious_password)
        self.assertEqual(params["host"], self.settings["host"])

    def test_rejects_unexpected_config_key(self):
        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "config.toml"
            config_file.write_text(
                '[database]\nhost="127.0.0.1"\nport=5432\ndbname="seminar_db"\n'
                'connect_timeout=5\nsslmode="disable"\noptions="-c search_path=evil"\n',
                encoding="utf-8",
            )
            with self.assertRaises(ConfigurationError):
                load_settings(config_file)

    def test_rejects_newlines_in_username(self):
        with self.assertRaises(ValueError):
            connection_parameters(self.settings, "seminar_user\nhost=malicious", "pass")


class MainUnitTests(unittest.TestCase):
    """Mocked client flow only; these tests do not verify a live database."""

    def test_bad_config_stops_before_prompting(self):
        errors = io.StringIO()
        with patch.object(app, "load_settings", side_effect=ConfigurationError("invalid sslmode")), \
                patch("builtins.input") as prompt, redirect_stderr(errors):
            result = app.main()
        self.assertEqual(result, 1)
        prompt.assert_not_called()
        self.assertIn("invalid sslmode", errors.getvalue())
        self.assertNotIn("Traceback", errors.getvalue())

    def test_successful_mocked_client_uses_separate_parameters_and_version_query(self):
        driver = MagicMock()
        cursor = driver.connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect = [("PostgreSQL 18 unit test",), ("seminar_user", "seminar_db")]
        output = io.StringIO()
        password = "private unit-test password host=other.example"
        with patch.dict("sys.modules", {"psycopg": driver}), \
                patch("builtins.input", return_value="seminar_user"), \
                patch.object(app.getpass, "getpass", return_value=password), redirect_stdout(output):
            result = app.main()
        self.assertEqual(result, 0)
        driver.connect.assert_called_once_with(
            **connection_parameters(load_settings(), "seminar_user", password)
        )
        self.assertEqual(cursor.execute.call_args_list, [
            call("SELECT VERSION();"), call("SELECT current_user, current_database();")
        ])
        self.assertIn("PostgreSQL 18 unit test", output.getvalue())
        self.assertNotIn(password, output.getvalue())


if __name__ == "__main__":
    unittest.main()
