import time
import json
import cache
import hashlib
import logging
import requests
import settings
import multiprocessing
from enum import Enum
from datetime import datetime
from slackclient import SlackClient

# ====================
# SLACK CLIENT CONFIG
# ====================

slack_token = settings.SLACK_API_TOKEN

# Instantiate Slack client
slack_client = SlackClient(token=slack_token)

# Bot's ID as an environment variable
BOT_NAME = settings.BOT_NAME
BOT_USER_ID = slack_client.api_call('auth.test')['user_id']
AT_BOT = "<@" + BOT_USER_ID + ">"

TEAM_INFO = slack_client.api_call('team.info').get('team')
TEAM_NAME = TEAM_INFO['name']
TEAM_ID = TEAM_INFO['id']

# 1 millisecond delay between reading from firehose
READ_WEBSOCKET_DELAY = 0.001


# Create Channel Enum
class Channel(Enum):
    PUBLIC = 10
    PRIVATE = 20
    DIRECT_MESSAGE = 30

# =======================================
# GENERAL CONSTANTS
# =======================================
MAX_CARD_CHARACTERS = settings.MAX_CARD_CHARACTERS
MAX_MESSAGE_CACHE = settings.MAX_MESSAGE_CACHE


def handle_messages(real_time_message):
    name = multiprocessing.current_process().name

    message_data = real_time_message[0]

    # Method for responding to private messages and for mentions in chat
    # Extract needed variables from the slack RTM object
    message_channel = message_data.get('channel')
    message_text = message_data.get('text')
    message_ts = message_data.get('ts')
    message_team = message_data.get('team')
    message_user = message_data.get('user')

    # Don't do anything if the user is this bot
    if BOT_USER_ID == message_user:
        return None

    # Determine the type of Channel the message is coming in on
    if message_channel[0] == 'C':
        message_location = Channel.PUBLIC
    elif message_channel[0] == 'D':
        message_location = Channel.DIRECT_MESSAGE
    elif message_channel[0] == 'G':
        message_location = Channel.PRIVATE
    else:
        logging.warning('New or Unknown Slack Channel Type! Defaulting to PUBLIC.')
        message_location = Channel.PUBLIC

    logging.debug('Channel Type: ' + str(message_location))

    logging.debug('At Bot: ' + str(AT_BOT))

    # If not a DM Check to see if bot was mentioned
    if message_location is not Channel.DIRECT_MESSAGE:
        if AT_BOT in message_text:
            message_text = clean_at_bot_text(message_text)
            logging.debug('Cleaned Text To: ' + str(message_text))
        else:
            # Don't Handle Public Messages without Bot Mention
            return None

    logging.debug('Recieved Message Data:\n     ' + str(message_data))

    # Generate a pointer to the message for potential future lookups
    message_pointer = (message_ts, message_channel)
    logging.debug('Message Pointer: ' + str(message_pointer))

    # Build WA converse POST request
    url = settings.WA_URL + "/v2/api/skillSets/" + settings.WA_SKILLSET + "/converse?api_key=" + settings.WA_API_KEY
    headers = {'Content-Type': 'application/json'}

    # Build the JSON body to send to WA converse endpoint
    data = dict()

    # Get slack userid and hash it for security
    hashed_user = hashlib.sha224(message_user.encode('utf-8')).hexdigest()

    # Set Context Template from context.json file
    context = settings.CONTEXT

    # Inject relevant data into context
    data['text'] = message_text
    data['language'] = settings.WA_LANGUAGE
    data['userID'] = hashed_user
    data['deviceType'] = settings.WA_DEVICE_TYPE
    data['clientID'] = settings.WA_CLIENT_ID
    data['additionalInformation'] = {"context": context}

    data = json.dumps(data)
    logging.debug("Data: \n" + str(data))

    response = requests.post(url, data=data, headers=headers)
    logging.debug(str(response))

    logging.debug('WA Response: \n' + str(response) + '    ')
    logging.debug('    ' + str(response.content))

    response_content = json.loads(response.content)

    # Handle ERRORS from WA Request
    # If WA is erroring out on request, send a fallback message and terminate
    if response.status_code >= 300 or response.status_code < 200:
        logging.warning("Error Getting Response from Server. Status Code: " + str(response.status_code))
        logging.warning("Response Content: \n" + str(response_content))

        # Send the text response to slack
        slack_client.api_call("chat.postMessage", channel=message_channel,
            text="Sorry I appear to be having connectivity issues. :cry: \n\nPlease try again in a few minutes.",
            as_user='true:'
        )

        # Post Analytics to Service
        if settings.ANALYTICS_ENABLED:
            analytics_user = analytics_user_input(message_text, hashed_user, message_channel, message_ts, message_team, "FAILURE", "")
            analytics_response = analytics_bot_response("Sorry I appear to be having connectivity issues. :cry: \n\nPlease try again in a few minutes.", message_channel, message_team, TEAM_NAME)
        return None

    # Extract Data from WA Response
    try:
        user_intent = response_content.get('skill').get('intents')[0].get('intent')
        intent_confidence = response_content.get('skill').get('intents')[0].get('confidence')
        skill = response_content.get('skill').get('name')
    except AttributeError:
        user_intent = "NO_INTENT_RECEIVED"
        intent_confidence = '0'
        skill = "NO_SKILL"

    logging.debug('User Intent: ' + str(user_intent))
    logging.debug('Intent Confidence: ' + str(intent_confidence))
    logging.debug('Skill: ' + str(skill))

    try:
        entities = response_content.get('skill').get('entities')
    except AttributeError:
        entities = []

    logging.debug('Entities: ' + str(entities))

    # Check for WA response data
    try:
        response_data = response.json()
    except ValueError:
        logging.warning("No response text from WA. Status Code: " + str(response.status_code))

        if settings.ANALYTICS_ENABLED:
            analytics_user_input(message_text, hashed_user, message_channel, message_ts, 'No WA Response Data', user_intent, entities)
        response_data = {"speech": {"text": "{ NO RESPONSE }"}}

    logging.debug('WA Response Data: \n    ' + str(response_data))

    # Inject Card Data into slack response text
    card_data = {}
    card_data_length = 2
    try:
        card_data = json.dumps(response_data.get('card'))
        logging.debug('Card Data:\n    ' + str(card_data))
        card_data_length = len(card_data)
    except ValueError:
        logging.warning('Value Error Getting Card Data')
    except AttributeError:
        logging.warning('Attribution Error: Card Data not Present')
        card_data = str({'Status Code': str(response.status_code), 'Response': str(response_data)})
        response_data = {'speech': {'text': '{ NO RESPONSE }'}, 'card': card_data}
        card_data_length = len(card_data)

    # Use response from WA to generate response for slack user
    text = response_data.get("speech").get("text")

    # Catch if there text is an empty value
    if not text:
        text = '{ No Text }'

    if message_location is not Channel.DIRECT_MESSAGE:
        text = '<@' + message_user + '> ' + text
    logging.debug('Slack Response Text: ' + str(text))

    # Appending Response data to text
    additional_text_info = '\n> *Intent:* `' + user_intent + '` *Confidence:* `' + str(
        intent_confidence) + '` *Skill:* `' + skill + '`\n> *Entities:* `' + str(json.dumps(entities)) + '`'
    text += additional_text_info

    # Add Card Data to the responses
    if card_data:
        if int(card_data_length) >= int(MAX_CARD_CHARACTERS):
            # text = text + "\n*Card Data:*\n```\n" + (card_data[:3497] + '...') + "\n```\n"
            logging.debug("Card data too long for code block.")
        else:
            text = text + "\n*Card Data:*\n```\n" + card_data + "\n```\n"

    logging.debug('Responded With: ' + str(text))

    # Send the text response to slack
    message_response = slack_client.api_call(
        "chat.postMessage",
        channel=message_channel,
        link_names=1,
        text=text,
        as_user='true:'
    )

    logging.debug('Response To Slack API Message Post:\n    ' + str(message_response))

    response_post_ts = message_response.get('ts')
    response_post_channel = message_response.get('channel')
    logging.debug('Response Posted Timestamp: ' + str(response_post_ts))
    logging.debug('Response Posted Channel: ' + str(response_post_channel))

    # Add Reactions for feedback
    reaction_response = slack_client.api_call(
        "reactions.add",
        channel=response_post_channel,
        name='+1::skin-tone-2',
        timestamp=response_post_ts
    )

    logging.debug('Reaction Response Thumbsup:\n    ' + str(reaction_response))

    reaction_response = slack_client.api_call(
        "reactions.add",
        channel=response_post_channel,
        name='-1::skin-tone-2',
        timestamp=response_post_ts
    )

    logging.debug('Reaction Response Thumbsdown:\n    ' + str(reaction_response))

    logging.debug('Slack Post Message Response: \n    ' + str(message_response))

    # Post a snippit if card data was long
    if int(card_data_length) >= int(MAX_CARD_CHARACTERS):
        slack_client.api_call(
            "files.upload",
            channels=message_channel,
            content=card_data,
            filetype='javascript',
            filename='Card Data.js',
            as_user='true:'
        )

    # Cache Message Pointers
    response_ts = message_response.get('ts')
    logging.debug('Bot Response TS: ' + str(response_ts))
    cache_response((message_ts, message_channel), response_ts)

    logging.debug('Message Cache: \n    ' + str(cache.message_cache))

    # Post Analytics to Service
    if settings.ANALYTICS_ENABLED:
        analytics_user = analytics_user_input(message_text, hashed_user, message_channel, message_ts, 'Slack Response', user_intent, entities)
        analytics_response = analytics_bot_response(response_data.get("speech").get("text"), message_channel, message_team, TEAM_NAME)

    return None


# Removes Bot Mentions from text strings
def clean_at_bot_text(message_text):
    if ' ' + AT_BOT in message_text:
        return message_text.replace(' ' + AT_BOT, '')
    elif AT_BOT + ' ' in message_text:
        return message_text.replace(AT_BOT + ' ', '')
    elif AT_BOT in message_text:
        return message_text.replace(AT_BOT, '')
    return message_text


def analytics_user_input(message, username, channel, event_ts, team, intent, entities):
    url = settings.ANALYTICS_INPUT_URL + settings.ANALYTICS_API_KEY
    headers = {'Content-Type': 'application/json'}

    # Build the JSON body to send to Bot Analytics Endpoint
    # Set Context from context.json file
    data = settings.ANALYTICS_USER_MESSAGE_JSON

    data['token'] = settings.ANALYTICS_API_KEY
    data['team']['id'] = team
    data['team']['name'] = TEAM_NAME

    data['bot']['id'] = settings.BOT_NAME

    data['message']['type'] = 'message'
    data['message']['channel'] = channel
    data['message']['user'] = username
    data['message']['text'] = message
    data['message']['ts'] = event_ts
    data['message']['team'] = team

    data['intent'] = {}
    data['intent']['name'] = intent

    # This is for entities
    data['intent']['inputs'] = []
    i = 0
    for entity in entities:
        logging.debug('    Entitiy ' + str(i) + ': ' + str(entity))
        data['intent']['inputs'].append({str(entity.get('entity')): str(entity.get('value'))})
        i += 1

    logging.debug('Intent Inputs: \n    ' + str(data['intent']['inputs']))

    data = json.dumps(data)
    logging.debug('User Input Data: \n    ' + str(data))

    response = requests.post(url, data=data, headers=headers)
    logging.debug('Analytics Status Code: ' + str(response))

    return True


def analytics_bot_response(message_response, channel, team, team_name):
    url = settings.ANALYTICS_RESPONSE_URL + settings.ANALYTICS_API_KEY
    headers = {'Content-Type': 'application/json'}

    # Build the JSON body to send to Bot Analytics Endpoint
    # Set Context from context.json file
    data = settings.ANALYTICS_BOT_RESPONSE_JSON

    data['token'] = settings.ANALYTICS_API_KEY

    data['team']['id'] = team
    data['team']['name'] = team_name

    data['bot']['id'] = settings.BOT_NAME

    data['message']['type'] = 'message'
    data['message']['channel'] = channel
    data['message']['text'] = message_response

    data = json.dumps(data)
    logging.debug("Bot Response Data: \n    " + str(data))

    response = requests.post(url, data=data, headers=headers)
    logging.debug('    ' + str(response))

    return True


# Takes in reaction events on slack and takes action if relevant for analytic purposes
def handle_reaction(rtm_event):
    name = multiprocessing.current_process().name

    logging.debug('Reaction Event:\n    ' + str(rtm_event))
    message_user = rtm_event.get('item_user')
    reacting_user = rtm_event.get('user')

    # If it is our bot being reacted to fetch the response of the bot
    if BOT_USER_ID == message_user and reacting_user != BOT_USER_ID:

        reaction = rtm_event.get('reaction')
        message = rtm_event.get('item')

        message_ts = message.get('ts')

        channel = message.get('channel')

        timestamp = rtm_event.get('event_ts')
        event_type = rtm_event.get('type')

        # Fetch the message being reacted to
        history = fetch_slack_message(channel, message_ts)

        if rtm_event.get('item').get('type') == 'message':
            history_message_parts = history.get('messages')[0].get('text').split('\n')
        else:
            return None

        response_text = history_message_parts[0]

        # Fetch the message that the bot was responding to
        if message_ts in cache.message_cache:
            input_responded_to_pointer = cache.message_cache[message_ts]
        else:
            input_responded_to_pointer = None

        logging.debug('Message Reacted About Pointer: \n    ' + str(input_responded_to_pointer))
        # If there is a cached pointer to the message being reacted to
        if input_responded_to_pointer:
            input_responded_to = fetch_slack_message(channel, input_responded_to_pointer[1][0])
            message_responded_to = input_responded_to.get('messages')[0].get('text')
            message_responded_to = clean_at_bot_text(message_responded_to)

            user = input_responded_to.get('messages')[0].get('user')
            hashed_username = hashlib.sha224(user.encode('utf-8')).hexdigest()

            if '-1' in reaction:
                logging.debug("Someone disliked response: " + str(response_text))

                # Post Analytics to Service
                if settings.ANALYTICS_ENABLED:
                    analytics_user_passed = analytics_user_input(message_responded_to, hashed_username, channel, timestamp, event_type, "BAD_RESPONSE", "")
                    analytics_response_passed = analytics_bot_response("Sorry I wasn't helpful, I'll try to learn from this for the future.", channel, TEAM_ID, TEAM_NAME)
                # Thank User for reaction
                slack_client.api_call(
                    "chat.postEphemeral",
                    channel=channel,
                    text="Sorry I wasn't helpful, I'll try to learn from this for the future.",
                    user=rtm_event.get('user'),
                    as_user='true:'
                )

            elif '+1' in reaction:
                logging.debug("Someone liked response: " + str(response_text))

                # Post Analytics to Service
                if settings.ANALYTICS_ENABLED:
                    analytics_user_passed = analytics_user_input(message_responded_to, hashed_username, channel, timestamp, TEAM_ID, "GOOD_RESPONSE", "")
                    analytics_response_passed = analytics_bot_response("Sorry I wasn't helpful, I'll try to learn from this for the future.", channel,TEAM_ID, TEAM_NAME)

                # Thank User for reaction
                slack_client.api_call(
                    "chat.postEphemeral",
                    channel=channel,
                    text="Thanks for the feedback! :grinning:",
                    user=rtm_event.get('user'),
                    as_user='true:'
                )

            logging.debug('Message Responded To: \n    ' + str(message_responded_to))
        else:
            input_responded_to = None

    else:
        pass

    return None


def fetch_slack_message(channel, message_timestamp):
    # Fetch the message being reacted to
    message = slack_client.api_call(
        "conversations.history",
        channel=channel,
        ts=message_timestamp,
        latest=message_timestamp,
        inclusive="true",
        count=1
    )

    logging.debug('Fetched Message: \n    ' + str(message))

    return message


# Caches Pointers From Bot Responses to User Messages
def cache_response(message_pointer, response_ts):

    logging.debug('Message Cache: \n    ' + str(cache.message_cache))

    # Delete old keys to maintain cache order
    if response_ts in cache.message_cache:
        cache.message_cache.move_to_end(response_ts, last=True)

    elif len(cache.message_cache) >= MAX_MESSAGE_CACHE:
        # Pop the oldest item in the dict to make room
        cache.message_cache.popitem(last=False)

    cache.message_cache[response_ts] = (datetime.now(), message_pointer)

    return None


if __name__ == "__main__":
    if slack_client.rtm_connect():
        logging.info("Bot connected and running!")

        jobs = []
        while True:
            real_time_message = slack_client.rtm_read()

            if real_time_message:
                message_type = real_time_message[0].get("type")

                # Handle Reactions to Responses
                if message_type == 'reaction_added':
                    process = multiprocessing.Process(name='Reaction Worker', target=handle_reaction, args=(real_time_message[0],))
                    jobs.append(process)
                    process.start()
                    # handle_reaction(real_time_message[0])

                elif message_type == 'message':
                    logging.debug('Message Event:\n    ' + str(real_time_message))
                    process = multiprocessing.Process(name='Message Worker', target=handle_messages, args=(real_time_message,))
                    jobs.append(process)
                    process.start()
                    # handle_messages(real_time_message)

                # Clean up completed worker threads
                cleaned_jobs = []
                for job in jobs:
                    if not job.is_alive():
                        # get results from thread
                        cleaned_jobs.append(job)
                jobs = cleaned_jobs
                logging.debug('Jobs: ' + str(jobs))

            # Pause for websocket firehose delay
            # time.sleep(READ_WEBSOCKET_DELAY)
        loop.close()

    else:
        logging.debug("Connection failed. Invalid Slack token or bot ID?")

