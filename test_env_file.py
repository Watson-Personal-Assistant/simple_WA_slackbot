 #
 # Copyright 2017 IBM Corp. All Rights Reserved.
 #
 # Licensed under the Apache License, Version 2.0 (the "License");
 # you may not use this file except in compliance with the License.
 # You may obtain a copy of the License at
 #
 #      http://www.apache.org/licenses/LICENSE-2.0
 #
 # Unless required by applicable law or agreed to in writing, software
 # distributed under the License is distributed on an "AS IS" BASIS,
 # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 # See the License for the specific language governing permissions and
 # limitations under the License.
 #
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
        self.assertIsNotNone(settings.WA_COLLECTION)

        # Ensure API Key Exists
        self.assertIsNotNone(settings.WA_API_KEY)

        # Ensure URL Exists
        self.assertIsNotNone(settings.WA_USER_ID)

        # Ensure Language Exists
        self.assertIsNotNone(settings.WA_LANGUAGE)

    def test_fallback_variables(self):
        # Ensure Fallback Responses String Exists
        self.assertIsNotNone(settings.FALLBACK_RESPONSES)
