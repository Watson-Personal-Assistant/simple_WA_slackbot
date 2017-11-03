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
import settings
import requests
from unittest import TestCase


# Test slack endpoint using loaded variables from .env file
class TestSlackConfiguration(TestCase):

    def test_slack(self):
        # Does the key exist?
        self.assertIsNotNone(settings.SLACK_API_TOKEN)

        # Does the bot id/name exist?
        self.assertIsNotNone(settings.BOT_ID)

        # Test API
        key = settings.SLACK_API_TOKEN
        url = "https://slack.com/api/auth.test"

        payload = "token=" + key
        headers = {
            'content-type': "application/x-www-form-urlencoded"
        }

        response = requests.request("POST", url, data=payload, headers=headers)

        print(response.text)

        # self.assertEquals(response.headers.get('Content-Type'), 'text/javascript;charset=utf-8')

        print("Status Code For Slack API Call: " + str(response.status_code))
        self.assertEquals(response.status_code, 200)
