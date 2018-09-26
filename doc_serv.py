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
from watson_developer_cloud import DiscoveryV1
import requests
import os
import io
from slackclient import SlackClient

# ====================
# Discovery service settings
# ====================
COLLECTION_ID = settings.COLLECTION_ID
CONFIGURATION_ID = settings.CONFIGURATION_ID
ENVIRONMENT_ID = settings.ENVIRONMENT_ID
DS_USERNAME = settings.DS_USERNAME
DS_PASSWORD = settings.DS_PASSWORD

# Create Disvoer Service proxy
class DS ():

    # =======================================
    # initialize DS Discovery Service proxy.
    # =======================================
    # creating a Discovery instance
    logging.debug( 'Creating a Discovery Service Instance' )
    discovery = DiscoveryV1(
      username=DS_USERNAME,
      password=DS_PASSWORD,
      version="2017-10-16"
    )

    #def read_img_file(doc_url):
        # creating a Visual Recognition  Service instance
        # instance = VisualRecognitionV3(api_key='paste your api _key here', version='2016-05-20')

        # select an image (local or url) with text in it. Recognizing text:
        #img = instance.recognize_text(images_url=doc_url)
        #text_read = img['images'][0]['text']
        #logging.debug( 'Read text %s ' %text_read  )
        #return(text_read)
        #delete_doc = discovery.delete_document('{environment_id}', '{collection_id}', '{document_id}').get_result()

    def determine_doctype(self, doc_info ):
        # QUery Disvoery Service for document that was just uploaded using document_id to see if it is ready
        doc_query =   'extracted_metadata.filename::' + doc_info['filename']
        #transport_doc_id = '876543210'
        #doc_query = {'query': "entities.text:'Johnny Depp'"}
        #doc_query =  "text:transport_doc_id"
        #doc_query = enriched_html_elements.tables.body_cells.cell_text:"Carlos"
        #doc_query='text:'+ transport_doc_id
        #search_term= doc_info['filename']
        #search_term = doc_name
        #doc_query =  "text:transport_doc_id"
        # field.delimiter.field.delimiter.text operator Value
        # enriched_text.concepts.text:Cloud computing
        #doc_query='text:'+ search_term
        #doc_query='document_id:'+ search_term
        #logging.debug('doc_query %s ' %doc_query)
        query_results = self.discovery.query(environment_id=ENVIRONMENT_ID, collection_id=COLLECTION_ID, query=doc_query ).get_result()
        #logging.debug(json.dumps(query_results, indent=2))
        logging.debug('matching results %s ' %query_results['matching_results'] )
        if query_results['matching_results'] > 0:
            # Get query_results details
            logging.debug('Found results ----------------------------------%s ' %query_results['results'][0]['text'][0])
            if "Transport Statement" in query_results['results'][0]['text'][0]:
                doc_type = "transport statement"
                logging.debug('Found matching text   id %s' %query_results['results'][0]['text'][0])
                logging.debug('Found matching file_type  %s' %query_results['results'][0]['extracted_metadata']["file_type"])
                logging.debug('Found matching title  %s' %query_results['results'][0]['extracted_metadata']["title"])
                logging.debug('Found matching filename  %s' %query_results['results'][0]['extracted_metadata']["filename"] )
                logging.debug('Found matching author  %s' %query_results['results'][0]['extracted_metadata']["author"])
            elif "Insurance Claim Form" in query_results['results'][0]['enriched_html_elements']['elements'][0]['sentence_text'] :
                #Get first name and last name out of the form
                doc_type = "Insurance Claim Form"
                x=0
                for element in query_results['results'][0]['enriched_html_elements']['elements']:
                    if element['sentence_text'] == 'First Name':
                        first_name = query_results['results'][0]['enriched_html_elements']['elements'][x+1]['sentence_text']
                        logging.debug('Insurance Claim Form first name is  %s' %first_name )
                    elif element['sentence_text'] == 'Last Name':
                        last_name = query_results['results'][0]['enriched_html_elements']['elements'][x+1]['sentence_text']
                        logging.debug('Insurance Claim Form last name is  %s' %last_name)
                        break
                    x = x + 1
                if last_name and first_name:
                    logging.debug('Insurance Claim form is complete ------------------------------------')
                else:
                    logging.debug('Insurance Claim form is missing ')
                logging.debug('Found matching publication date  %s' %query_results['results'][0]['extracted_metadata']["publicationdate"] )
                logging.debug('Found matching file_type  %s' %query_results['results'][0]['extracted_metadata']["file_type"] )
                logging.debug('Found matching title  %s' %query_results['results'][0]['extracted_metadata']["title"])
                logging.debug('Found matching filename  %s' %query_results['results'][0]['extracted_metadata']["filename"] )
                logging.debug('Found matching author  %s' %query_results['results'][0]['extracted_metadata']["author"])
            elif doc_type == None :
                logging.debug('doc_type is unknown')
                doc_type ="unknown"

        else:
            logging.warning('Document was not found YYYYYYYYYYY.')
        '''
        matching results
        {
          "matching_results" : 24,
          "results" : [ {
            "id" : "watson-generated ID",
            "score" : 1
          } ],
          "aggregations" : {
            "term" : {
              "results" : [ {
                "key" : "active",
                "matching_results" : 34
              } ]
            }
          }
        }
        '''
        return(doc_type)

    def read_file_from_slack(self, doc_url, doc_name, slack_token):
        doc_type = "uknown"
        # Get the pdf from Slack doc_url which is the private URL
        r = requests.get(doc_url, headers={'Authorization': 'Bearer {}'.format(slack_token) })
        logging.debug("read_file_from_slack headers %s " %r.headers )
        logging.debug("read_file_from_slack content-type %s " %r.headers['content-type'] )

        # Save the file in the cloud temporarily
        with open(doc_name, 'wb' ) as f:
            f.write(r.content)
        filepath = os.path.join(os.getcwd(), '.', doc_name )
        logging.debug('filepath %s' %filepath)
        logging.debug('filepath assertion %s' %os.path.isfile(filepath) )

        # Put pdf document in Discovery instance - works but testing other methods
        with open(filepath, 'rb') as fileinfo:
            add_doc = self.discovery.add_document(ENVIRONMENT_ID, COLLECTION_ID, file=fileinfo).get_result()

        logging.debug('Add Document metadata ------')
        logging.debug(add_doc)
        #for key in add_doc.keys():
        #    logging.debug( 'item  ---------------------------- ')
        #    logging.debug('Key %s' %key )
        #    logging.debug('Value %s' %add_doc.get(key) )
        # Get document details
        logging.debug('add_doc before get_document_status %s' %add_doc['document_id'])
        # Get document status details
        doc_info = self.discovery.get_document_status(ENVIRONMENT_ID, COLLECTION_ID, add_doc['document_id'] ).get_result()
        logging.debug(json.dumps(doc_info, indent=2))
        #doc_dic =  dict()
        #doc_dic.appen( json.loads( doc_info)[0] ) )
        '''
        JSON
        {
            "result": {
                        "document_id": "f3ef01f4-3273-4983-82f0-f8e5e9b00530",
                        "status": "processing"
                        or
                         "status" : "available with notices",
                         "status_description" : "Document is successfully ingested but was indexed with warnings",
                         or
                          "status" : "Document is successfully ingested and indexed with no warnings",
                         },

            "headers": {
        '''
        for key in doc_info.keys():
            logging.debug( 'doc dic keys info  ---------------------------- ')
            logging.debug('Key %s' %key )
            logging.debug('Value %s' %doc_info.get(key) )
        time_waiting = 0
        status = 'not done'
        doc_type = 'unknown'
        while time_waiting < 15 and status != 'done' :
            if doc_info.get('status') == "available":
                # Find document that was just uploaded from the user and see if it is ready for processing .
                status = 'done'
                logging.debug('Document is successfully ingested and indexed with no warnings Here is document ID')
                '''
                {u'status': u'available',
                 u'sha1': u'caf3fd7088099f174cc008e07e35dc8c6d6d0662',
                 u'file_type': u'pdf',
                 u'filename': u'ciscoshipping.pdf',
                 u'notices': [],
                 u'status_description': u'Document is successfully ingested and indexed with no warnings',
                 u'document_id': u'dcb81408-e34c-4584-a132-3af685d386f6'
                }
                '''
                logging.debug(doc_info)
                logging.debug("document_id  %s" %doc_info['document_id'])
                #logging.debug(  "configuration_id %s" %doc_info['configuration_id'])
                logging.debug(  "status  %s" %doc_info['status'])
                logging.debug(  "status_description  %s" %doc_info['status_description'])
                logging.debug(  "filename %s" %doc_info['filename'])
                logging.debug(  "file_type %s " %doc_info['file_type'])
                logging.debug(  "sha1%s " %doc_info['sha1'])
                if doc_info.get('notices') :
                    logging.debug(  "notice id %s" %doc_info['notices'][0]['notice_id'])
                    logging.debug(    "severity %s" %doc_info['notices'][0]['severity'])
                    logging.debug(     "step %s"  %doc_info['notices'][0]['step'])
                    logging.debug(     "description %s"  %doc_info['notices'][0]['description'] )
                    logging.debug(     "document_id %s"    %doc_info['notices'][0]['document_id'])
                doc_type = self.determine_doctype(doc_info)
            else:
                logging.warning('Document was not ready yet XXXXXXXXXXX. %s ' %doc_info['status'])
                time_waiting = time_waiting + 1.5
                # Get document details
                doc_info = self.discovery.get_document_status(ENVIRONMENT_ID, COLLECTION_ID, add_doc['document_id']).get_result()
                time.sleep(8)
        return "document is " + doc_type

    def message_wassol(self, message_text, message_user):
        # Process file metadata and then pass it in to Watson Assistant Solution with CONTEXT
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

        return None

    def handle_files(self, real_time_message):
        logging.debug('handle_files: started ')
        logging.debug('check if there are files %s ' %real_time_message[0].get("files")    )
        name = multiprocessing.current_process().name
        message_data = real_time_message[0]
        url_private_download  = real_time_message[0].get("files")[0]['url_private_download']
        logging.debug('handle_files: url_private_download  %s' %url_private_download )

        # Method for responding to private messages and for mentions in chat
        # Extract needed variables from the slack RTM object
        message_channel = message_data.get('channel')
        message_ts = message_data.get('ts')
        message_team = message_data.get('team')
        message_text = message_data.get('text')
        message_user = message_data.get('user')
        logging.debug('handle_files: message_user   %s' %message_user)
        message_files = message_data.get('files')
        logging.debug('handle_files: message_files id  %s' %message_files[0].get('id') )
        message_name = message_data.get('name')
        logging.debug('handle_files: message_files url_private  %s' %message_files[0].get('url_private') )
        logging.debug('handle_files: message_files name  %s' %message_files[0].get('name') )
        #intent_text = self.read_file_from_slack( message_files[0].get('url_private'), message_files[0].get('name'), settings.SLACK_API_TOKEN  )
        # for testing
        intent_text = "Insurance Claim Form"
        logging.debug(' intent_text %s ' %intent_text)
        self.message_wassol(intent_text, message_user)
        return

if __name__ == "__main__":
    logging.debug("Done")
    #doc_url ='https://files.slack.com/files-pri/TCV7G5HCL-FCXAK0M0D/transport-statement_1_.pdf'
    #doc_name = 'transport-statement(1).pdf'
    #doc_url ='https://files.slack.com/files-pri/TCV7G5HCL-FCZ9NUXBP/download/ciscoshipping.pdf'
    #doc_name = 'ciscoshipping.pdf'

    # ====================
    # SLACK CLIENT CONFIG
    # ====================
    slack_token = settings.SLACK_API_TOKEN
    doc_url ='https://files.slack.com/files-pri/TCV7G5HCL-FD0RF552B/claimformibm.pdf'
    doc_name = 'claimformibm.pdf'
    ds_test = DS()
    file_type = ds_test.read_file_from_slack(doc_url, doc_name, slack_token)
    logging.debug("Done %s" %file_type)
