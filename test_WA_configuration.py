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
        self.assertIsNotNone(settings.WA_SKILLSET)

        # Ensure API Key Exists
        self.assertIsNotNone(settings.WA_API_KEY)

        # Ensure Device Type Exists
        self.assertIsNotNone(settings.WA_DEVICE_TYPE)

    def test_health_check(self):
        # Test WA API
        # Build WA converse POST request
        url = settings.WA_URL + "/v2/api/skillSets/" + settings.WA_SKILLSET + "/health?api_key=" + settings.WA_API_KEY

        headers = {'Accept': 'application/json'}

        response = requests.get(url, headers=headers)
        print(str(response))

        print(response.text)

        self.assertEquals(response.headers.get('Content-Type'), 'application/json; charset=utf-8')

        print("Status Code For WA Healthcheck API Call: " + str(response.status_code))
        self.assertEquals(response.status_code, 200)

    def test_converse(self):
        # Test WA API
        # Build WA converse POST request
        url = settings.WA_URL + "/v2/api/skillSets/" + settings.WA_SKILLSET + "/converse?api_key=" + settings.WA_API_KEY
        headers = {'Content-Type': 'application/json'}

        # Build the JSON body to send to WA converse endpoint
        data = dict()
        data['text'] = "Test"
        data['language'] = "en-US"
        data['userID'] = "slackbot-test"
        data['deviceType'] = settings.WA_DEVICE_TYPE
        data['additionalInformation'] = \
            {
                "context":
                {
                    "application": {"id": "application-14c", "attributes": {}}
                }
            }

        data = json.dumps(data)
        print("Data: \n" + str(data))

        response = requests.post(url, data=data, headers=headers)
        print(str(response))

        print(response.text)

        print("Status Code For WA Converse API Call: " + str(response.status_code))
        self.assertTrue(response.status_code >= 200 < 300)
