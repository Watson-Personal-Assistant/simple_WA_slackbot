import json
import logging
import settings
import requests
from datetime import datetime, timedelta


class IAM_Token_Singleton:
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state


class IAM_Token(IAM_Token_Singleton):
    def __init__(self, access_token, refresh_token, expiration_time):
        IAM_Token_Singleton.__init__(self)
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expiration_time = expiration_time

    def __str__(self):
        string = '{\'access_token\': \'' + str(self.access_token) + '\', \'refresh_token\': \'' + str(self.refresh_token) + '\', \'expiration_time\': \'' + str(self.expiration_time) + '\'}'
        return string

    def expired(self):
        current_time = datetime.now()
        return bool(current_time > self.expiration_time)

    def refresh(self):
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

        logging.debug("Status Code:" + str(response.status_code))
        logging.debug("OAuth2:" + response.text)

        json_data = json.loads(response.text)
        self.access_token = json_data.get('access_token')
        self.refresh_token = json_data.get('refresh_token')
        expires_in = json_data.get('expires_in')
        expiration = json_data.get('expiration')
        self.expiration_time = current_time + timedelta(seconds=expires_in)

        return None

    def get_access_token(self):
        if self.expired():
            self.refresh()

        return self.access_token
