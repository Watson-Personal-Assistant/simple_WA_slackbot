from unittest import TestCase
from os.path import join, dirname
import settings
import os


class TestEnvFile(TestCase):
    def test_env_file(self):

        # Ensure .env file exists
        env_path = join(dirname(__file__), '..', '.env')
        print("ENV Path: " + str(env_path))

        env_exists = os.path.exists(env_path)
        print("ENV file Exists: " + str(env_exists))

        self.assertTrue(env_exists)

    def test_slack_variables(self):
        # Does the key exist?
        self.assertIsNotNone(settings.SLACK_API_TOKEN)

        # Does the bot id/name exist?
        self.assertIsNotNone(settings.BOT_ID)

    def test_WA_variables(self):
        # Ensure URL Exists
        self.assertIsNotNone(settings.WA_URL)

        # Ensure Avatar Exists
        self.assertIsNotNone(settings.WA_SKILLSET)

        # Ensure API Key Exists
        self.assertIsNotNone(settings.WA_API_KEY)

        # Ensure Language Exists
        self.assertIsNotNone(settings.WA_LANGUAGE)

        # Ensure Device Type Exists
        self.assertIsNotNone(settings.WA_DEVICE_TYPE)

    def test_fallback_variables(self):
        # Ensure Fallback Responses String Exists
        self.assertIsNotNone(settings.FALLBACK_RESPONSES)

    def test_bot_config_variables(self):
        # Ensure Fallback Responses String Exists
        self.assertIsNotNone(settings.MAX_CARD_CHARACTERS)
        self.assertTrue(0 <= int(settings.MAX_CARD_CHARACTERS) <= 9999999999)
