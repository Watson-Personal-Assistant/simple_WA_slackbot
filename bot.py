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
import re
import csv
import time
import json
import logging
import requests
import settings
from slackclient import SlackClient

# ====================
# SLACK CLIENT CONFIG
# ====================

slack_token = settings.SLACK_API_TOKEN

# starterbot's ID as an environment variable
BOT_ID = settings.BOT_ID

# constants
AT_BOT = "<@" + BOT_ID + ">"

# instantiate Slack & Twilio clients
slack_client = SlackClient(slack_token)

# 1 second delay between reading from firehose
READ_WEBSOCKET_DELAY = 1


# =================
# LOGGING SETTINGS
# =================

# Config logging
logging.basicConfig(filename='slackbot.log', level=logging.DEBUG)

# create logger
logger = logging.getLogger('slackbot_log')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


# =======================================
# IDENTIFYING UNHANDLED UTTERANCES SETUP
# =======================================
fallback_responses = settings.FALLBACK_RESPONSES.split(', ')


def reply(real_time_message):
    # Method for responding to private messages and for mentions in chat

    # Extract needed variables from the slack RTM object
    message_type = real_time_message[0].get("type")
    message_channel = real_time_message[0].get("channel")
    message_text = real_time_message[0].get("text")
    message_ts = real_time_message[0].get("msg")
    message_content = real_time_message[0].get("content")
    message_subtitle = real_time_message[0].get("subtitle")

    channel_message = "#" in message_subtitle

    # Get username based on channel or PM
    if channel_message:
        # Channel
        print("Message Content: " + message_content.encode('utf-8'))
        message_username = message_content.split(':')[0]
    else:
        # Private Message
        message_username = message_subtitle

    # Print anything non None vars
    if message_type is not None:
        print("Message Type: " + str(message_type))
    if message_channel is not None:
        print("Message Channel: " + str(message_channel))
    if message_text is not None:
        print("Message Text: " + str(message_text))
    if message_ts is not None:
        print("Message TS: " + str(message_ts))
    if message_content is not None:
        print("Message Content: " + str(message_content.encode('utf8')))
    if message_subtitle is not None:
        print("Message Subtitle: " + str(message_subtitle))
    if message_username is not None:
        print("Message Username: " + str(message_username))

    message_content = re.sub(r'.*@' + settings.BOT_ID + ' ', '', message_content)

    # Check to make sure there is not channel wide notification present
    channel_notifications = ['@here', '@channel', '@everyone']
    global_notification = any(x in message_content for x in channel_notifications)

    if str(message_subtitle) != 'bot (bot)' and str(message_username) != 'bot' and not global_notification:

        logger.info('\nReceived Message: ' + message_content)

        # Build WA converse POST request
        url = settings.WA_URL + "/v2/api/converse/expertiseCollection/" + settings.WA_COLLECTION + "?api_key=" + settings.WA_API_KEY
        headers = {'Content-Type': 'application/json'}

        # Build the JSON body to send to WA converse endpoint
        data = dict()

        # Uncomment if you want to use a username defined in the .env file, then comment out the line after
        # username = settings.WA_USER_ID
        username = message_username

        data['text'] = message_content
        data['language'] = settings.WA_LANGUAGE
        data['userID'] = username
        data['deviceType'] = "slackbot"
        data['additionalInformation'] = {
            "context": {}
        }

        data = json.dumps(data)
        print("Data: \n" + str(data))

        response = requests.post(url, data=data, headers=headers)
        print(str(response))

        try:
            response_data = response.json()
        except ValueError:
            logger.warn("No response text from WA. Status Code: " + str(response.status_code))
            user_input_row = [str(time.time()), "NO RESPONSE", message_content.encode('utf8')]
            with open(r'fallback_responses.csv', 'a') as f:
                writer = csv.writer(f)
                writer.writerow(user_input_row)
            response_data = {"speech": {"text": "{ NO RESPONSE }"}}

        print("Data: ")
        print(str(response_data).encode('utf-8'))

        card_data = ""
        card_data_length = 0

        try:
            if response_data.get('card'):   
                card_data = json.dumps(response_data.get('card'))
                print("\nCard Data: ")
                print(card_data)
                card_data_length = len(card_data)
        except ValueError:
            logger.warn("Error Getting Card Data")

        text = response_data.get("speech").get("text")

        # Catch if there text is an empty value
        if not text:
            text = "{ No Text }"

        if channel_message:
            text = "@" + message_username + " " + text
        print("Text: " + str(text.encode('utf8')))

        # Add Card Data to the responses
        if card_data:
            if card_data_length >= 3500:
                # text = text + "\n*Card Data:*\n```\n" + (card_data[:3497] + '...') + "\n```\n"
                print("Card data too long for code block.")
            else:
                text = text + "\n*Card Data:*\n```\n" + card_data + "\n```\n"

        # Puts unhandled intents into fallback_responses.csv with timestamp
        if text in fallback_responses:
            print("Logging unhandled response.")
            user_input_row = [str(time.time()), "FALLBACK", message_content.encode('utf8')]
            with open(r'fallback_responses.csv', 'a') as f:
                writer = csv.writer(f)
                writer.writerow(user_input_row)

        logger.info('Responded: ' + str(text.encode('utf-8')) + '\n')

        # Send the text response to slack
        slack_client.api_call(
            "chat.postMessage",
            token=slack_token,
            channel=message_channel,
            text=text,
            as_user='true:'
        )

        # Post a snippit if card data was long
        if card_data_length >= 3500:
            slack_client.api_call(
                "files.upload",
                token=slack_token,
                channels=message_channel,
                content=card_data,
                filetype='javascript',
                filename='Card Data.js',
                as_user='true:'
            )
    else:
        if global_notification:
            print("Not responding to channel wide notification.")
        else:
            print("Not responding to my own message.")
    return None


if __name__ == "__main__":
    if slack_client.rtm_connect():
        print("Bot connected and running!")
        while True:
            real_time_message = slack_client.rtm_read()

            if real_time_message:
                print("RTM: " + str(real_time_message))
                message_type = real_time_message[0].get("type")
                print("Message Type: " + str(message_type) + "\n")

                if message_type == "desktop_notification":
                    reply(real_time_message)

            time.sleep(READ_WEBSOCKET_DELAY)

    else:
        print("Connection failed. Invalid Slack token or bot ID?")

