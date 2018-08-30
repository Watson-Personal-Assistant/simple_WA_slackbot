import settings
import requests
from unittest import TestCase


# Test slack endpoint using loaded variables from .env file
class TestSlackConfiguration(TestCase):

    def test_slack(self):
        # Does the key exist?
        self.assertIsNotNone(settings.SLACK_API_TOKEN)

        # Does the bot id/name exist?
        self.assertIsNotNone(settings.BOT_NAME)

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
