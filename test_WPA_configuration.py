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
import json
import settings
import requests
from unittest import TestCase


# Test slack endpoint using loaded variables from .env file
class TestSlackConfiguration(TestCase):

    def test_credentials(self):
        # Ensure URL Exists
        self.assertIsNotNone(settings.WA_URL)

        # Ensure Avatar Exists
        self.assertIsNotNone(settings.WA_COLLECTION)

        # Ensure API Key Exists
        self.assertIsNotNone(settings.WA_API_KEY)

        # Ensure URL Exists
        self.assertIsNotNone(settings.WA_USER_ID)

    def test_health_check(self):
        # Test WA API
        # Build WA converse POST request
        url = settings.WA_URL + "/v1/api/healthcheck?api_key=" + settings.WA_API_KEY

        headers = {'Accept': 'application/json'}

        response = requests.get(url, headers=headers)
        print(str(response))

        print(response.text)

        self.assertEquals(response.headers.get('Content-Type'), 'application/json')

        print("Status Code For WA Healthcheck API Call: " + str(response.status_code))
        self.assertEquals(response.status_code, 200)

    def test_converse(self):
        # Test WA API
        # Build WA converse POST request
        url = settings.WA_URL + "/v2/api/converse/expertiseCollection/" + settings.WA_COLLECTION + "?api_key=" + settings.WA_API_KEY
        headers = {'Content-Type': 'application/json'}

        # Build the JSON body to send to WA converse endpoint
        data = dict()
        data['id'] = settings.WA_USER_ID
        data['version'] = "1.0"
        data['language'] = "en-US"
        data['text'] = "Test"
        data['context'] = {
            "user": {"id": settings.WA_USER_ID},
            "application": {"id": "application-14c", "attributes": {}}
        }

        data = json.dumps(data)
        print("Data: \n" + str(data))

        response = requests.post(url, data=data, headers=headers)
        print(str(response))

        print(response.text)

        print("Status Code For WA Converse API Call: " + str(response.status_code))
        self.assertTrue(response.status_code >= 200 < 300)
