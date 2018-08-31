echo "Loading from .env file..."
source .env

printf '%s\n'
echo "Enter Bluemix App Name:"
read APPNAME

printf '%s\n'
printf 'Pushing Application...'
cf push $APPNAME --no-route true --health-check-type process

printf '%s\n'
printf '%s\n' "Uploading Variables..."

printf '%s\n'

printf '%s\n' "WA_URL"
printf '%s\n' "    $WA_URL"
cf set-env $APPNAME WA_URL $WA_URL
printf '%s\n'

printf '%s\n' "WA_SKILLSET"
printf '%s\n' "    $WA_SKILLSET"
cf set-env $APPNAME WA_SKILLSET $WA_SKILLSET
printf '%s\n'

printf '%s\n' "WA_API_KEY"
printf '%s\n' "    $WA_API_KEY"
cf set-env $APPNAME WA_API_KEY $WA_API_KEY
printf '%s\n'

printf '%s\n' "WA_LANGUAGE"
printf '%s\n' "    $WA_LANGUAGE"
cf set-env $APPNAME WA_LANGUAGE $WA_LANGUAGE
printf '%s\n'

printf '%s\n' "WA_DEVICE_TYPE"
printf '%s\n' "    $WA_DEVICE_TYPE"
cf set-env $APPNAME WA_DEVICE_TYPE $WA_DEVICE_TYPE
printf '%s\n'

printf '%s\n' "FALLBACK_RESPONSES"
printf '%s\n' "    $FALLBACK_RESPONSES"
cf set-env $APPNAME FALLBACK_RESPONSES \"$FALLBACK_RESPONSES\"
printf '%s\n'

printf '%s\n' "MAX_CARD_CHARACTERS"
printf '%s\n' "    $MAX_CARD_CHARACTERS"
cf set-env $APPNAME MAX_CARD_CHARACTERS $MAX_CARD_CHARACTERS
printf '%s\n'

printf '%s\n' "SLACK_API_TOKEN"
printf '%s\n' "    $SLACK_API_TOKEN"
cf set-env $APPNAME SLACK_API_TOKEN $SLACK_API_TOKEN
printf '%s\n'

printf '%s\n' "BOT_ID"
printf '%s\n' "    $BOT_ID"
cf set-env $APPNAME BOT_ID $BOT_ID

printf '%s\n'
printf 'Restaging Application...'
cf push $APPNAME --no-route true --health-check-type process


printf '%s\n'