"""Live database checks: run separately with unittest discover -s integration -v.

Only interactive input is replaced. psycopg and the database are real.
Provide APP_DB_PASSWORD through the environment; credentials are never printed.
"""

import io
import os
import unittest
import uuid
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from src import app


class DatabaseIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password = os.environ.get("APP_DB_PASSWORD")
        if not cls.password:
            raise unittest.SkipTest("APP_DB_PASSWORD is not set; live database checks were not run.")
        cls.settings = app.load_settings()

    def run_client(self, username, password):
        output, errors = io.StringIO(), io.StringIO()
        with patch("builtins.input", return_value=username), \
                patch.object(app.getpass, "getpass", return_value=password), \
                redirect_stdout(output), redirect_stderr(errors):
            result = app.main()
        # Do not include captured text in assertions about secret disclosure.
        self.assertFalse(password in output.getvalue(), "Password was written to stdout.")
        self.assertFalse(password in errors.getvalue(), "Password was written to stderr.")
        return result, output.getvalue(), errors.getvalue()

    def test_real_main_returns_postgresql_18_and_identity(self):
        result, output, errors = self.run_client("seminar_user", self.password)
        self.assertEqual(result, 0, "Live application connection failed; check the container and credentials.")
        self.assertEqual(errors, "")
        self.assertIn("Подключение успешно!", output)
        self.assertIn("Результат SELECT VERSION():", output)
        self.assertRegex(output, r"PostgreSQL 18(?:\.|\s)")
        self.assertIn("Пользователь: seminar_user\n", output)
        self.assertIn(f"База данных: {self.settings['dbname']}\n", output)

    def test_real_main_refuses_wrong_password(self):
        wrong_password = "invalid-" + uuid.uuid4().hex
        result, output, errors = self.run_client("seminar_user", wrong_password)
        self.assertEqual(result, 1)
        self.assertNotIn("Подключение успешно!", output)
        self.assertIn("OperationalError", errors)

    def test_real_main_refuses_username_options_and_preserves_host(self):
        username = "seminar_user host=malicious.invalid port=9999"
        before = app.load_settings()
        result, output, errors = self.run_client(username, self.password)
        self.assertEqual(result, 1)
        self.assertNotIn("Подключение успешно!", output)
        self.assertIn("OperationalError", errors)
        self.assertIn(f"Сервер: {before['host']}:{before['port']}\n", output)
        self.assertEqual(app.load_settings(), before)
        params = app.connection_parameters(before, username, self.password)
        self.assertEqual(params["host"], before["host"])
        self.assertEqual(params["port"], before["port"])
        self.assertEqual(params["user"], username)


if __name__ == "__main__":
    unittest.main()
