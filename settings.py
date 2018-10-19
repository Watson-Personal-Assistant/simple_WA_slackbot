import os
import json
import logging
from dotenv import load_dotenv
from os.path import join, dirname


def set_log_level(logger_level):
    logging.getLogger().setLevel(logger_level)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logger_level)

    # create formatter
    formatter = logging.Formatter('\n%(asctime)s - %(name)s - %(levelname)s - \n%(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logging.getLogger().addHandler(ch)


# Configure Logging Default
set_log_level(logging.INFO)

# If on bluemix load env differently
# Load Environment variables set via VCAP variables in Bluemix
#if 'VCAP_SERVICES' in os.environ:
    # print("On Bluemix...")

# Check for existance of .env file
env_path = join(dirname(__file__), '.env')

# Load .env file into os.environ
load_dotenv(env_path)

# ===================
# Logging Settings
# ===================
try:
    # API Key for bot analytics
    LOG_LEVEL = os.environ.get("LOG_LEVEL").upper()
    log_level_str = LOG_LEVEL

    if LOG_LEVEL == 'INFO':
        LOG_LEVEL = logging.INFO
    elif LOG_LEVEL == 'DEBUG':
        LOG_LEVEL = logging.DEBUG
    elif LOG_LEVEL == 'WARNING':
        LOG_LEVEL = logging.WARNING
    elif LOG_LEVEL == 'ERROR':
        LOG_LEVEL = logging.ERROR
    else:
        LOG_LEVEL = logging.WARNING

    logging.info("Logging Set To: " + log_level_str)

    if LOG_LEVEL != logging.WARNING:
        set_log_level(LOG_LEVEL)
except Exception as ex:
    template = 'Error: {0} Problem reading Logging Level string from environment variables. Logging set to WARNING LEVEL. Arguments: \n{1!r}'
    message = template.format(type(ex).__name__, ex.args)
    ANALYTICS_ENABLED = False
    logging.warning(message)


# ===================
# Analytics Settings
# ===================
try:
    # API Key for bot analytics
    ANALYTICS_ENABLED = (os.environ.get("ANALYTICS_ENABLED").upper() == 'TRUE')
    logging.info("Analytics Enabled: " + str(ANALYTICS_ENABLED))
except Exception as ex:
    template = 'Error: {0} Problem reading ANALYTICS_ENABLED boolean from environment variables. Analytics posting is disabled. Arguments: \n{1!r}'
    message = template.format(type(ex).__name__, ex.args)
    ANALYTICS_ENABLED = False
    logging.warning(message)

if ANALYTICS_ENABLED:
    try:
        ANALYTICS_API_KEY = os.environ.get("ANALYTICS_API_KEY")
        ANALYTICS_INPUT_URL = os.environ.get("ANALYTICS_INPUT_URL")
        ANALYTICS_RESPONSE_URL = os.environ.get("ANALYTICS_RESPONSE_URL")
    except Exception as ex:
        template = 'Error: {0} Problem reading ANALYTICS credentials or urls from environment variables. Analytics posting is disabled. Arguments: \n{1!r}'
        message = template.format(type(ex).__name__, ex.args)
        ANALYTICS_ENABLED = False
        logging.error(message)

# =======================================
# Slack & Watson Assistant Credentials
# =======================================

# WA Authentication
try:
    AUTH_TYPE = os.environ.get("AUTH_TYPE")
    if AUTH_TYPE == "IAM":
        try:
            WA_TENANT_ID = os.environ.get("WA_TENANT_ID")
            IAM_API_KEY = os.environ.get("IAM_API_KEY")
        except Exception as ex:
            logging.error("ERROR: Loading WA_TENANT_ID or IAM_API_KEY")
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logging.error(message)
    elif AUTH_TYPE == "API_KEY":
        try:
            WA_API_KEY = os.environ.get("WA_API_KEY")
            # logging.debug("WA_API_KEY: " + WA_API_KEY)
        except Exception as ex:
            logging.error("ERROR: Loading WA_API_KEY")
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logging.error(message)
    else:
        raise ValueError('AUTH_TYPE was not \'IAM\' or \'API_KEY\'')
except Exception as ex:
    logging.error("ERROR: Missing Required Authentication Type (AUTH_TYPE) environment variable. Use Either: IAM or API_KEY as values.")
    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
    message = template.format(type(ex).__name__, ex.args)
    logging.error(message)

try:
    # Slack Credentials
    SLACK_API_TOKEN = os.environ.get("SLACK_API_TOKEN")
    BOT_NAME = os.environ.get("BOT_NAME")

    # WA Credentials
    WA_URL = os.environ.get("WA_URL")
    WA_SKILLSET = os.environ.get("WA_SKILLSET")
    WA_LANGUAGE = os.environ.get("WA_LANGUAGE")
    WA_DEVICE_TYPE = os.environ.get("WA_DEVICE_TYPE")


    if os.environ.get("WA_CLIENT_ID"):
        WA_CLIENT_ID = os.environ.get("WA_DEVICE_TYPE")
    else:
        WA_CLIENT_ID = 'slackbot'

    FALLBACK_RESPONSES = os.environ.get("FALLBACK_RESPONSES")

    # Bot Configuration Settings
    MAX_CARD_CHARACTERS = os.environ.get("MAX_CARD_CHARACTERS")

    print("Environment Variables Loaded Successfully")

except Exception as ex:
    print("ERROR: Missing Required Environment Variables")
    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
    message = template.format(type(ex).__name__, ex.args)
    print(message)

# ========================
# Message Cache Settings
# ========================
try:
    # Upper Limit for Cache Size for tuple references of bot replies to user messages
    MAX_MESSAGE_CACHE = int(os.environ.get('MAX_MESSAGE_CACHE'))
except Exception as ex:
    template = 'Error: {0} Problem reading Max Message Cache Size Integer from environment variables. MAX_MESSAGE_CACHE was set to 1000. Arguments: \n{1!r}'
    message = template.format(type(ex).__name__, ex.args)
    ANALYTICS_ENABLED = False
    logging.warning(message)


# ==================
# Load JSON Files
# ==================

# Set Context from context.json file
try:
    with open('context.json') as json_file:
        CONTEXT = json.load(json_file)

    with open('analytics_bot_response.json') as json_file:
        ANALYTICS_BOT_RESPONSE_JSON = json.load(json_file)

    with open('analytics_user_message.json') as json_file:
        ANALYTICS_USER_MESSAGE_JSON = json.load(json_file)

except Exception as ex:
    template = "Couldn't read .json file. An exception of type {0} occurred. Arguments:\n{1!r}"
    message = template.format(type(ex).__name__, ex.args)
    logging.warning(message)
