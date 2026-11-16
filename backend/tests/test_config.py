"""설정 읽기를 확인한다. 환경 변수가 먼저이고 backend/.env 는 빈 값만 채운다. (D-035, D-044)"""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import config

# 테스트용 가짜 값이다.
FAKE = "fake-secret-for-test"


class LoadEnvFileTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.env = Path(self._tmp.name) / ".env"

    def load(self, text):
        self.env.write_text(text, encoding="utf-8")
        config._load_env_file(self.env)

    def test_reads_key_value_lines(self):
        with patch.dict(os.environ, clear=False):
            os.environ.pop("CONFIG_TEST_KEY", None)
            self.load("# 주석\n\nCONFIG_TEST_KEY=value-1\n")
            self.assertEqual(os.environ["CONFIG_TEST_KEY"], "value-1")

    def test_strips_quotes_and_spaces(self):
        with patch.dict(os.environ, clear=False):
            os.environ.pop("CONFIG_TEST_KEY", None)
            self.load('  CONFIG_TEST_KEY = "quoted"  \n')
            self.assertEqual(os.environ["CONFIG_TEST_KEY"], "quoted")

    def test_environment_variable_wins_over_file(self):
        with patch.dict(os.environ, {"CONFIG_TEST_KEY": "from-env"}):
            self.load("CONFIG_TEST_KEY=from-file\n")
            self.assertEqual(os.environ["CONFIG_TEST_KEY"], "from-env")

    def test_ignores_lines_without_equals(self):
        with patch.dict(os.environ, clear=False):
            os.environ.pop("CONFIG_TEST_KEY", None)
            self.load("CONFIG_TEST_KEY\n")
            self.assertNotIn("CONFIG_TEST_KEY", os.environ)

    def test_missing_file_is_fine(self):
        config._load_env_file(Path(self._tmp.name) / "none.env")


class SessionSecretTest(unittest.TestCase):
    def test_returns_bytes(self):
        with patch.dict(os.environ, {"SESSION_SECRET": FAKE}):
            self.assertEqual(config.session_secret(), FAKE.encode("utf-8"))

    def test_missing_secret_stops_startup(self):
        with patch.dict(os.environ, clear=False):
            os.environ.pop("SESSION_SECRET", None)
            with self.assertRaises(RuntimeError):
                config.session_secret()

    def test_empty_secret_stops_startup(self):
        with patch.dict(os.environ, {"SESSION_SECRET": ""}):
            with self.assertRaises(RuntimeError):
                config.session_secret()

    def test_error_message_does_not_contain_a_value(self):
        with patch.dict(os.environ, clear=False):
            os.environ.pop("SESSION_SECRET", None)
            with self.assertRaises(RuntimeError) as caught:
                config.session_secret()
        self.assertNotIn(FAKE, str(caught.exception))


class AnthropicKeyTest(unittest.TestCase):
    def test_trims_spaces_and_newlines(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": f"  {FAKE}\r\n"}):
            self.assertEqual(config.anthropic_api_key(), FAKE)

    def test_missing_key_is_empty_string(self):
        with patch.dict(os.environ, clear=False):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            self.assertEqual(config.anthropic_api_key(), "")


if __name__ == "__main__":
    unittest.main()
