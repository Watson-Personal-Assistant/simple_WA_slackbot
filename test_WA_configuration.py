import json
import logging
import settings
import requests
import iam_auth
from unittest import TestCase
from datetime import datetime, timedelta


# Test slack endpoint using loaded variables from .env file
class TestWAConfiguration(TestCase):

    def test_credentials(self):
        # Ensure Auth Type Exists
        self.assertIsNotNone(settings.AUTH_TYPE)

        # Ensure Auth Type is Valid
        self.assertTrue(settings.AUTH_TYPE == "IAM" or settings.AUTH_TYPE == "API_KEY")

        if settings.AUTH_TYPE == 'IAM':
            # Ensure IAM API Key Exists
            self.assertIsNotNone(settings.IAM_API_KEY)

            # Ensure Tenant ID Exists
            self.assertIsNotNone(settings.WA_TENANT_ID)
        else:
            # Ensure API Key Exists
            self.assertIsNotNone(settings.WA_API_KEY)

        # Ensure URL Exists
        self.assertIsNotNone(settings.WA_URL)

        # Ensure Avatar Exists
        self.assertIsNotNone(settings.WA_SKILLSET)

        # Ensure Device Type Exists
        self.assertIsNotNone(settings.WA_DEVICE_TYPE)

    def test_IAM_auth(self):

        if settings.AUTH_TYPE == 'IAM':
            # Init Auth
            current_time = datetime.now()

            url = "https://iam.bluemix.net/oidc/token"

            querystring = {
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "response_type": "cloud_iam",
                "apikey": settings.IAM_API_KEY
            }

            headers = {
                'content-type': "application/x-www-form-urlencoded"
            }

            response = requests.request("POST", url, headers=headers, params=querystring)

            json_data = json.loads(response.text)
            access_token = json_data.get('access_token')
            refresh_token = json_data.get('refresh_token')
            expires_in = json_data.get('expires_in')
            expiration = json_data.get('expiration')
            expiration_time = current_time + timedelta(seconds=expires_in)

            global iam_token
            iam_token = iam_auth.IAM_Token(access_token, refresh_token, expiration_time)

    def test_health_check(self):
        # Test WA API
        # Build WA converse POST request

        if settings.AUTH_TYPE == "API_KEY":
            url = settings.WA_URL + "/v2/api/skillSets/" + settings.WA_SKILLSET + "/health?api_key=" + settings.WA_API_KEY
            headers = {
                'Content-Type': 'application/json',
                'accept': 'application/json'
            }
        else:
            global iam_token
            auth = 'Bearer ' + str(iam_token.get_access_token())

            url = settings.WA_URL + "/v2/api/skillSets/" + settings.WA_SKILLSET + "/health"
            headers = {
                'Content-Type': 'application/json',
                'accept': 'application/json',
                'Authorization': auth,
                'tenantid': settings.WA_TENANT_ID
            }

        response = requests.get(url, headers=headers)
        print(str(response))

        print(response.text)

        self.assertEquals(response.headers.get('Content-Type'), 'application/json; charset=utf-8')

        print("Status Code For WA Healthcheck API Call: " + str(response.status_code))
        self.assertEquals(response.status_code, 200)

    def test_converse(self):
        # Test WA API
        # Build WA converse POST request

        if settings.AUTH_TYPE == "API_KEY":
            url = settings.WA_URL + "/v2/api/skillSets/" + settings.WA_SKILLSET + "/converse?api_key=" + settings.WA_API_KEY
            headers = {
                'Content-Type': 'application/json',
                'accept': 'application/json'
            }
        else:
            global iam_token
            auth = 'Bearer ' + str(iam_token.get_access_token())

            url = settings.WA_URL + "/v2/api/skillSets/" + settings.WA_SKILLSET + "/converse"
            headers = {
                'Content-Type': 'application/json',
                'accept': 'application/json',
                'Authorization': auth,
                'tenantid': settings.WA_TENANT_ID
            }

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
