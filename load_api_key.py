# Stolen from Travis

import logging
import os
from requests.auth import HTTPBasicAuth
import requests
import json

base_url = 'https://a.blazemeter.com/api/v4/'


def get_api_key():
    if os.path.isfile(os.getcwd() + '/api-key.json'):
        logging.info("Loading api key from file.")
        my_file = open(os.getcwd() + '/api-key.json', 'r')
        contents = my_file.read()
        key = json.loads(contents)
        key_id = key['id']
        secret = key['secret']
        auth = HTTPBasicAuth(key_id, secret)
        check = check_api_key(auth)
        if check:
            return auth
        else:
            logging.error('API Key in api-key.json is not valid. Notifying monitoring channel and exiting...')
            # Exit code 3 means api key file contains a non-admin API key
            exit(3)
    else:
        logging.error("Failed to find API key file.")
        logging.error('api-key.json file failed to load. Notifying monitoring channel and exiting...')
        # Exit code 2 means api key file is missing
        exit(2)


def check_api_key(auth):
    logging.debug('Function bulk_processes_auth.check_api_key')
    check = True
    logging.info('GET ' + base_url + 'user')
    r = requests.get(base_url + 'user', auth=auth)
    response = r.json()
    logging.info(response)
    if r.status_code == 200:
        logging.info('API Key is valid.')
        logging.info('Checking for admin access')
        if response['result']['features']['admin']:
            logging.info('API Key has admin access.')
            return check
        else:
            logging.error('API Key does not have admin access.')
            check = False
            return check
    else:
        logging.error('API Key is not valid.')
        print('Your API Key is not valid. Please check the api-key.json file.')
        check = False
        return check
