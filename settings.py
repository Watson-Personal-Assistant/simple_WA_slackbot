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
import os
from dotenv import load_dotenv
from os.path import join, dirname

# If on bluemix load env differently
# Load Environment variables set via VCAP variables in Bluemix
if 'VCAP_SERVICES' in os.environ:
    print("On Bluemix...")

# Load Environment Variables in a sane non Bluemix way
else:
    print("Not On Bluemix...")

    # Check for existance of .env file
    env_path = join(dirname(__file__), '.env')

    # Load .env file into os.environ
    load_dotenv(env_path)

try:
    # Slack Credentials
    SLACK_API_TOKEN = os.environ.get("SLACK_API_TOKEN")
    BOT_ID = os.environ.get("BOT_ID")

    # WA Credentials
    WA_URL = os.environ.get("WA_URL")
    WA_COLLECTION = os.environ.get("WA_COLLECTION")
    WA_API_KEY = os.environ.get("WA_API_KEY")
    WA_USER_ID = os.environ.get("WA_USER_ID")
    WA_LANGUAGE = os.environ.get("WA_LANGUAGE")

    FALLBACK_RESPONSES = os.environ.get("FALLBACK_RESPONSES")

    print("Environment Variables Loaded Successfully")

except Exception as ex:
    print("ERROR: Missing Required Environment Variables")
    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
    message = template.format(type(ex).__name__, ex.args)
    print(message)


